// SPDX-License-Identifier: MIT
pragma solidity ^0.8.9;

import {IToposCore, CertificateId, SubnetId} from "./../../interfaces/IToposCore.sol";
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {IBurnableMintableCappedERC20} from "./../../interfaces/IBurnableMintableCappedERC20.sol";
import {ITokenDeployer} from "./../../interfaces/ITokenDeployer.sol";

import {DepositHandler} from "./DepositHandler.sol";
import {AdminMultisigBase} from "./AdminMultisigBase.sol";
import "./Bytes32Sets.sol";

contract ToposCore is IToposCore, AdminMultisigBase {
    using Bytes32SetsLib for Bytes32SetsLib.Set;

    enum TokenType {
        InternalBurnable,
        InternalBurnableFrom,
        External
    }

    /// @dev Storage slot with the address of the current implementation. `keccak256('eip1967.proxy.implementation') - 1`.
    bytes32 internal constant KEY_IMPLEMENTATION =
        bytes32(0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc);

    /// @notice Mapping to store certificates
    /// @dev CertificateId(bytes32) => certificate(bytes)
    mapping(CertificateId => Certificate) public certificates;

    /// @notice Mapping to store the last seen certificate for a subnet
    /// @dev SubnetId(bytes32) => StreamPosition
    mapping(SubnetId => IToposCore.StreamPosition) checkpoint;

    /// @notice Mapping to store Tokens
    /// @dev TokenKey(bytes32) => Token
    mapping(bytes32 => Token) public tokens;

    /// @notice Mapping of transaction root to the certificate ID
    /// @dev txRootHash(bytes32) => CertificateId(bytes32)
    mapping(bytes32 => CertificateId) public txRootToCertId;

    /// @notice The subnet ID of the subnet this contract is deployed on
    /// @dev Must be set in the constructor
    SubnetId internal immutable _networkSubnetId;

    /// @notice Validator role
    /// 0xa95257aebefccffaada4758f028bce81ea992693be70592f620c4c9a0d9e715a
    bytes32 internal constant VALIDATOR = keccak256(abi.encodePacked("VALIDATOR"));

    // AUDIT: slot names should be prefixed with some standard string
    bytes32 internal constant PREFIX_TOKEN_KEY = keccak256("token-key");
    bytes32 internal constant PREFIX_TOKEN_TYPE = keccak256("token-type");
    bytes32 internal constant PREFIX_CONTRACT_CALL_EXECUTED = keccak256("contract-call-executed");
    bytes32 internal constant PREFIX_CONTRACT_CALL_EXECUTED_WITH_MINT = keccak256("contract-call-executed-with-mint");
    bytes32 internal constant PREFIX_SEND_TOKEN_EXECUTED = keccak256("send-token-executed");
    bytes32 internal constant PREFIX_TOKEN_DAILY_MINT_LIMIT = keccak256("token-daily-mint-limit");
    bytes32 internal constant PREFIX_TOKEN_DAILY_MINT_AMOUNT = keccak256("token-daily-mint-amount");

    /// @notice Internal token deployer (ERCBurnableMintable by default)
    address internal immutable _tokenDeployerImplementation;

    /// @notice Set of certificate IDs
    Bytes32SetsLib.Set certificateSet;

    /// @notice Set of Token Keys derived from token symbols
    Bytes32SetsLib.Set tokenSet;

    /// @notice Set of source subnet IDs (subnets sending the certificates)
    Bytes32SetsLib.Set sourceSubnetIdSet;

    constructor(address tokenDeployerImplementation, SubnetId networkSubnetId) {
        if (tokenDeployerImplementation.code.length == 0) revert InvalidTokenDeployer();

        _tokenDeployerImplementation = tokenDeployerImplementation;
        _networkSubnetId = networkSubnetId;
    }

    /*******************\
    |* Admin Functions *|
    \*******************/

    function setTokenDailyMintLimits(string[] calldata symbols, uint256[] calldata limits) external override onlyAdmin {
        if (symbols.length != limits.length) revert InvalidSetDailyMintLimitsParams();

        for (uint256 i = 0; i < symbols.length; i++) {
            string memory symbol = symbols[i];
            uint256 limit = limits[i];

            if (getTokenBySymbol(symbol).tokenAddress == address(0)) revert TokenDoesNotExist(symbol);

            _setTokenDailyMintLimit(symbol, limit);
        }
    }

    function upgrade(
        address newImplementation,
        bytes32 newImplementationCodeHash,
        bytes calldata setupParams
    ) external override onlyAdmin {
        if (newImplementationCodeHash != newImplementation.codehash) revert InvalidCodeHash();
        _setImplementation(newImplementation);

        // AUDIT: If `newImplementation.setup` performs `selfdestruct`, it will result in the loss of _this_ implementation (thereby losing the ToposCore)
        //        if `upgrade` is entered within the context of _this_ implementation itself.
        if (setupParams.length != 0) {
            // solhint-disable-next-line avoid-low-level-calls
            (bool success, ) = newImplementation.delegatecall(
                abi.encodeWithSelector(IToposCore.setup.selector, setupParams)
            );

            if (!success) revert SetupFailed();
        }
        emit Upgraded(newImplementation);
    }

    function deployToken(bytes calldata params) external {
        (string memory name, string memory symbol, uint256 cap, address tokenAddress, uint256 dailyMintLimit) = abi
            .decode(params, (string, string, uint256, address, uint256));

        // Ensure that this symbol has not been taken.
        if (getTokenBySymbol(symbol).tokenAddress != address(0)) revert TokenAlreadyExists(symbol);

        if (tokenAddress == address(0)) {
            // If token address is no specified, it indicates a request to deploy one.
            bytes32 salt = keccak256(abi.encodePacked(symbol));

            // solhint-disable-next-line avoid-low-level-calls
            (bool success, bytes memory data) = _tokenDeployerImplementation.delegatecall(
                abi.encodeWithSelector(ITokenDeployer.deployToken.selector, name, symbol, cap, salt)
            );

            if (!success) revert TokenDeployFailed(symbol);

            tokenAddress = abi.decode(data, (address));

            _setTokenType(symbol, TokenType.InternalBurnableFrom);
        } else {
            // If token address is specified, ensure that there is a contact at the specified address.
            if (tokenAddress.code.length == uint256(0)) revert TokenContractDoesNotExist(tokenAddress);

            // Mark that this symbol is an external token, which is needed to differentiate between operations on mint and burn.
            _setTokenType(symbol, TokenType.External);
        }

        _setTokenAddress(symbol, tokenAddress);
        _setTokenDailyMintLimit(symbol, dailyMintLimit);

        emit TokenDeployed(symbol, tokenAddress);
    }

    /// @dev Give token to an account for testing
    function giveToken(
        string memory symbol,
        address account,
        uint256 amount
    ) external onlyAdmin {
        _mintToken(symbol, account, amount);
    }

    /**********************\
    |* External Functions *|
    \**********************/

    function pushCertificate(bytes memory certBytes, uint256 position) external {
        (
            CertificateId prevId,
            SubnetId sourceSubnetId,
            bytes32 stateRoot,
            bytes32 txRoot,
            SubnetId[] memory targetSubnets,
            uint32 verifier,
            CertificateId certId,
            bytes memory starkProof,
            bytes memory signature
        ) = abi.decode(
                certBytes,
                (CertificateId, SubnetId, bytes32, bytes32, SubnetId[], uint32, CertificateId, bytes, bytes)
            );

        certificateSet.insert(CertificateId.unwrap(certId)); // add certificate ID to the CRUD storage set
        Certificate storage newCert = certificates[certId];
        newCert.prevId = prevId;
        newCert.sourceSubnetId = sourceSubnetId;
        newCert.stateRoot = stateRoot;
        newCert.txRoot = txRoot;
        newCert.targetSubnets = targetSubnets;
        newCert.verifier = verifier;
        newCert.certId = certId;
        newCert.starkProof = starkProof;
        newCert.signature = signature;

        if (!sourceSubnetIdExists(sourceSubnetId)) {
            sourceSubnetIdSet.insert(SubnetId.unwrap(sourceSubnetId)); // add the source subnet ID to the CRUD storage set
        }
        IToposCore.StreamPosition storage newStreamPosition = checkpoint[sourceSubnetId];
        newStreamPosition.certId = certId;
        newStreamPosition.position = position;
        newStreamPosition.sourceSubnetId = sourceSubnetId;

        txRootToCertId[txRoot] = certId; // add certificate ID to the transaction root mapping
        emit CertStored(certId, txRoot);
    }

    function setup(bytes calldata params) external override {
        (address[] memory adminAddresses, uint256 newAdminThreshold) = abi.decode(params, (address[], uint256));
        // Prevent setup from being called on a non-proxy (the implementation).
        if (implementation() == address(0)) revert NotProxy();

        // NOTE: Admin epoch is incremented to easily invalidate current admin-related state.
        uint256 newAdminEpoch = _adminEpoch() + uint256(1);
        _setAdminEpoch(newAdminEpoch);
        _setAdmins(newAdminEpoch, adminAddresses, newAdminThreshold);
    }

    function executeAssetTransfer(
        bytes32 txRootHash,
        uint256 indexOfDataInTxRaw,
        bytes calldata txRaw,
        bytes calldata /*crossSubnetTxProof*/
    ) external {
        if (txRaw.length < indexOfDataInTxRaw + 4) revert IllegalMemoryAccess();
        CertificateId certId = txRootToCertId[txRootHash];
        if (!certificateExists(certId)) revert CertNotPresent();
        // In order to validate the transaction pass the entire transaction bytes which is then hashed.
        // The transaction hash is used as a leaf to validate the inclusion proof.
        bytes32 txHash = keccak256(abi.encodePacked(txRaw));
        (SubnetId targetSubnetId, address receiver, string memory symbol, uint256 amount) = abi.decode(
            txRaw[indexOfDataInTxRaw + 4:], // omit the 4 bytes function selector
            (SubnetId, address, string, uint256)
        );
        if (!_validateTargetSubnetId(targetSubnetId)) revert InvalidSubnetId();
        if (_isSendTokenExecuted(txHash)) revert TransferAlreadyExecuted();
        // prevent re-entrancy
        _setSendTokenExecuted(txHash);
        _mintToken(symbol, receiver, amount);
    }

    function sendToken(
        SubnetId targetSubnetId,
        address receiver,
        string calldata symbol,
        uint256 amount
    ) external {
        _burnTokenFrom(msg.sender, symbol, amount);
        emit TokenSent(msg.sender, _networkSubnetId, targetSubnetId, receiver, symbol, amount);
    }

    function callContract(
        SubnetId targetSubnetId,
        address targetContractAddr,
        bytes calldata payload
    ) external {
        emit ContractCall(_networkSubnetId, msg.sender, targetSubnetId, targetContractAddr, payload);
    }

    function callContractWithToken(
        SubnetId targetSubnetId,
        address targetContractAddr,
        bytes calldata payload,
        string calldata symbol,
        uint256 amount
    ) external {
        _burnTokenFrom(msg.sender, symbol, amount);
        emit ContractCallWithToken(
            _networkSubnetId,
            msg.sender,
            targetSubnetId,
            targetContractAddr,
            payload,
            symbol,
            amount
        );
    }

    /// @dev Returns the current `adminEpoch`.
    function adminEpoch() external view override returns (uint256) {
        return _adminEpoch();
    }

    /// @dev Returns the admin threshold for a given `adminEpoch`.
    function adminThreshold(uint256 epoch) external view override returns (uint256) {
        return _getAdminThreshold(epoch);
    }

    /// @dev Returns the array of admins within a given `adminEpoch`.
    function admins(uint256 epoch) external view override returns (address[] memory results) {
        uint256 adminCount = _getAdminCount(epoch);
        results = new address[](adminCount);

        for (uint256 i; i < adminCount; ++i) {
            results[i] = _getAdmin(epoch, i);
        }
    }

    /******************\
    |* Public Methods *|
    \******************/

    function verifyContractCallData(CertificateId certId, SubnetId targetSubnetId) public view returns (bool) {
        if (!certificateExists(certId)) revert CertNotPresent();
        if (!_validateTargetSubnetId(targetSubnetId)) revert InvalidSubnetId();
        return true;
    }

    /***********\
    |* Getters *|
    \***********/

    function certificateExists(CertificateId certId) public view returns (bool) {
        return certificateSet.exists(CertificateId.unwrap(certId));
    }

    function getCertificateCount() public view returns (uint256) {
        return certificateSet.count();
    }

    function getCertIdAtIndex(uint256 index) public view returns (CertificateId) {
        return CertificateId.wrap(certificateSet.keyAtIndex(index));
    }

    function sourceSubnetIdExists(SubnetId subnetId) public view returns (bool) {
        return sourceSubnetIdSet.exists(SubnetId.unwrap(subnetId));
    }

    function getSourceSubnetIdCount() public view returns (uint256) {
        return sourceSubnetIdSet.count();
    }

    function getSourceSubnetIdAtIndex(uint256 index) public view returns (SubnetId) {
        return SubnetId.wrap(sourceSubnetIdSet.keyAtIndex(index));
    }

    function tokenDailyMintLimit(string memory symbol) public view override returns (uint256) {
        return getUint(_getTokenDailyMintLimitKey(symbol));
    }

    function tokenDailyMintAmount(string memory symbol) public view override returns (uint256) {
        return getUint(_getTokenDailyMintAmountKey(symbol, block.timestamp / 1 days));
    }

    function getTokenBySymbol(string memory symbol) public view override returns (Token memory) {
        bytes32 tokenKey = _getTokenKey(symbol);
        return tokens[tokenKey];
    }

    function implementation() public view override returns (address) {
        return getAddress(KEY_IMPLEMENTATION);
    }

    function tokenDeployer() public view override returns (address) {
        return _tokenDeployerImplementation;
    }

    function getTokenCount() public view returns (uint256) {
        return tokenSet.count();
    }

    function getTokenKeyAtIndex(uint256 index) public view returns (bytes32) {
        return tokenSet.keyAtIndex(index);
    }

    function getNetworkSubnetId() public view returns (SubnetId) {
        return _networkSubnetId;
    }

    function getCertificate(CertificateId certId)
        public
        view
        returns (
            CertificateId,
            SubnetId,
            bytes32,
            bytes32,
            SubnetId[] memory,
            uint32,
            CertificateId,
            bytes memory,
            bytes memory,
            uint256
        )
    {
        Certificate memory storedCert = certificates[certId];
        (
            storedCert.prevId,
            storedCert.sourceSubnetId,
            storedCert.stateRoot,
            storedCert.txRoot,
            storedCert.targetSubnets,
            storedCert.verifier,
            storedCert.certId,
            storedCert.starkProof,
            storedCert.signature
        );
    }

    function getCheckpoints() public view returns (IToposCore.StreamPosition[] memory checkpoints) {
        uint256 sourceSubnetIdCount = getSourceSubnetIdCount();
        checkpoints = new StreamPosition[](sourceSubnetIdCount);
        for (uint256 i; i < sourceSubnetIdCount; i++) {
            checkpoints[i] = checkpoint[getSourceSubnetIdAtIndex(i)];
        }
    }

    /********************\
    |* Internal Methods *|
    \********************/

    function _callERC20Token(address tokenAddress, bytes memory callData) internal returns (bool) {
        // solhint-disable-next-line avoid-low-level-calls
        (bool success, bytes memory returnData) = tokenAddress.call(callData);
        return success && (returnData.length == uint256(0) || abi.decode(returnData, (bool)));
    }

    function _mintToken(
        string memory symbol,
        address account,
        uint256 amount
    ) internal {
        address tokenAddress = getTokenBySymbol(symbol).tokenAddress;

        if (tokenAddress == address(0)) revert TokenDoesNotExist(symbol);

        _setTokenDailyMintAmount(symbol, tokenDailyMintAmount(symbol) + amount);

        if (_getTokenType(symbol) == TokenType.External) {
            bool success = _callERC20Token(
                tokenAddress,
                abi.encodeWithSelector(IERC20.transfer.selector, account, amount)
            );

            if (!success) revert MintFailed(symbol);
        } else {
            IBurnableMintableCappedERC20(tokenAddress).mint(account, amount);
        }
    }

    function _burnTokenFrom(
        address sender,
        string memory symbol,
        uint256 amount
    ) internal {
        address tokenAddress = getTokenBySymbol(symbol).tokenAddress;

        if (tokenAddress == address(0)) revert TokenDoesNotExist(symbol);
        if (amount == 0) revert InvalidAmount();

        TokenType tokenType = _getTokenType(symbol);
        bool burnSuccess;

        if (tokenType == TokenType.External) {
            burnSuccess = _callERC20Token(
                tokenAddress,
                abi.encodeWithSelector(IERC20.transferFrom.selector, sender, address(this), amount)
            );
            if (!burnSuccess) revert BurnFailed(symbol);
        } else if (tokenType == TokenType.InternalBurnableFrom) {
            burnSuccess = _callERC20Token(
                tokenAddress,
                abi.encodeWithSelector(IBurnableMintableCappedERC20.burnFrom.selector, sender, amount)
            );
            if (!burnSuccess) revert BurnFailed(symbol);
        } else {
            burnSuccess = _callERC20Token(
                tokenAddress,
                abi.encodeWithSelector(
                    IERC20.transferFrom.selector,
                    sender,
                    IBurnableMintableCappedERC20(tokenAddress).depositAddress(bytes32(0)),
                    amount
                )
            );
            if (!burnSuccess) revert BurnFailed(symbol);
            IBurnableMintableCappedERC20(tokenAddress).burn(bytes32(0));
        }
    }

    /********************\
    |* Internal Setters *|
    \********************/

    function _setTokenDailyMintLimit(string memory symbol, uint256 limit) internal {
        _setUint(_getTokenDailyMintLimitKey(symbol), limit);

        emit TokenDailyMintLimitUpdated(symbol, limit);
    }

    function _setTokenDailyMintAmount(string memory symbol, uint256 amount) internal {
        uint256 limit = tokenDailyMintLimit(symbol);
        if (limit > 0 && amount > limit) revert ExceedDailyMintLimit(symbol);

        _setUint(_getTokenDailyMintAmountKey(symbol, block.timestamp / 1 days), amount);
    }

    function _setTokenType(string memory symbol, TokenType tokenType) internal {
        _setUint(_getTokenTypeKey(symbol), uint256(tokenType));
    }

    function _setTokenAddress(string memory symbol, address tokenAddress) internal {
        bytes32 tokenKey = _getTokenKey(symbol);
        tokenSet.insert(tokenKey);
        Token storage token = tokens[tokenKey];
        token.symbol = symbol;
        token.tokenAddress = tokenAddress;
    }

    function _setSendTokenExecuted(bytes32 txHash) internal {
        _setBool(_getIsSendTokenExecutedKey(txHash), true);
    }

    function _setImplementation(address newImplementation) internal {
        _setAddress(KEY_IMPLEMENTATION, newImplementation);
    }

    /********************\
    |* Internal Getters *|
    \********************/

    function _getTokenType(string memory symbol) internal view returns (TokenType) {
        return TokenType(getUint(_getTokenTypeKey(symbol)));
    }

    function _validateTargetSubnetId(SubnetId targetSubnetId) internal view returns (bool) {
        return SubnetId.unwrap(targetSubnetId) == SubnetId.unwrap(_networkSubnetId);
    }

    function _isSendTokenExecuted(bytes32 txHash) internal view returns (bool) {
        return getBool(_getIsSendTokenExecutedKey(txHash));
    }

    /********************\
    |* Pure Key Getters *|
    \********************/

    function _getTokenDailyMintLimitKey(string memory symbol) internal pure returns (bytes32) {
        return keccak256(abi.encodePacked(PREFIX_TOKEN_DAILY_MINT_LIMIT, symbol));
    }

    function _getTokenDailyMintAmountKey(string memory symbol, uint256 day) internal pure returns (bytes32) {
        return keccak256(abi.encodePacked(PREFIX_TOKEN_DAILY_MINT_AMOUNT, symbol, day));
    }

    function _getTokenTypeKey(string memory symbol) internal pure returns (bytes32) {
        return keccak256(abi.encodePacked(PREFIX_TOKEN_TYPE, symbol));
    }

    function _getTokenKey(string memory symbol) internal pure returns (bytes32) {
        return keccak256(abi.encodePacked(PREFIX_TOKEN_KEY, symbol));
    }

    function _getIsSendTokenExecutedKey(bytes32 txHash) internal pure returns (bytes32) {
        return keccak256(abi.encode(PREFIX_SEND_TOKEN_EXECUTED, txHash));
    }
}
