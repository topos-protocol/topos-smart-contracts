// SPDX-License-Identifier: MIT
pragma solidity ^0.8.9;

import {IToposCoreContract, subnetId} from "./../../interfaces/IToposCoreContract.sol";
import {IAuth} from "./../../interfaces/IAuth.sol";
import {IERC20} from "./../../interfaces/IERC20.sol";
import {IBurnableMintableCappedERC20} from "./../../interfaces/IBurnableMintableCappedERC20.sol";
import {ITokenDeployer} from "./../../interfaces/ITokenDeployer.sol";

import {ECDSA} from "./ECDSA.sol";
import {DepositHandler} from "./DepositHandler.sol";
import {AdminMultisigBase} from "./AdminMultisigBase.sol";

contract ToposCoreContract is IToposCoreContract, AdminMultisigBase {
    enum TokenType {
        InternalBurnable,
        InternalBurnableFrom,
        External
    }

    /// @dev Removed slots; Should avoid re-using
    // bytes32 internal constant KEY_ALL_TOKENS_FROZEN = keccak256('all-tokens-frozen');
    // bytes32 internal constant PREFIX_TOKEN_FROZEN = keccak256('token-frozen');

    /// @dev Storage slot with the address of the current factory. `keccak256('eip1967.proxy.implementation') - 1`.
    bytes32 internal constant KEY_IMPLEMENTATION =
        bytes32(0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc);

    // AUDIT: slot names should be prefixed with some standard string
    bytes32 internal constant PREFIX_COMMAND_EXECUTED = keccak256("command-executed");
    bytes32 internal constant PREFIX_TOKEN_ADDRESS = keccak256("token-address");
    bytes32 internal constant PREFIX_TOKEN_TYPE = keccak256("token-type");
    bytes32 internal constant PREFIX_CONTRACT_CALL_APPROVED = keccak256("contract-call-approved");
    bytes32 internal constant PREFIX_CONTRACT_CALL_APPROVED_WITH_MINT = keccak256("contract-call-approved-with-mint");
    bytes32 internal constant PREFIX_TOKEN_DAILY_MINT_LIMIT = keccak256("token-daily-mint-limit");
    bytes32 internal constant PREFIX_TOKEN_DAILY_MINT_AMOUNT = keccak256("token-daily-mint-amount");

    bytes32 internal constant SELECTOR_BURN_TOKEN = keccak256("burnToken");
    bytes32 internal constant SELECTOR_DEPLOY_TOKEN = keccak256("deployToken");
    bytes32 internal constant SELECTOR_MINT_TOKEN = keccak256("mintToken");
    bytes32 internal constant SELECTOR_APPROVE_CONTRACT_CALL = keccak256("approveContractCall");
    bytes32 internal constant SELECTOR_APPROVE_CONTRACT_CALL_WITH_MINT = keccak256("approveContractCallWithMint");
    bytes32 internal constant SELECTOR_TRANSFER_OPERATORSHIP = keccak256("transferOperatorship");

    address internal immutable _authModule;
    address internal immutable _tokenDeployerImplementation;

    modifier onlySelf() {
        if (msg.sender != address(this)) revert NotSelf();

        _;
    }

    constructor(
        address, /*authModule*/
        address tokenDeployerImplementation
    ) {
        // if (authModule.code.length == 0) revert InvalidAuthModule();
        if (tokenDeployerImplementation.code.length == 0) revert InvalidTokenDeployer();

        _authModule = address(0); /*authModule*/
        _tokenDeployerImplementation = tokenDeployerImplementation;
    }

    /**********************\
    |* External Functions *|
    \**********************/

    function setup(bytes calldata params) external override {
        // Prevent setup from being called on a non-proxy (the implementation).
        if (implementation() == address(0)) revert NotProxy();

        (address[] memory adminAddresses, uint256 newAdminThreshold, bytes memory newOperatorsData) = abi.decode(
            params,
            (address[], uint256, bytes)
        );

        // NOTE: Admin epoch is incremented to easily invalidate current admin-related state.
        uint256 newAdminEpoch = _adminEpoch() + uint256(1);
        _setAdminEpoch(newAdminEpoch);
        _setAdmins(newAdminEpoch, adminAddresses, newAdminThreshold);

        if (newOperatorsData.length > 0) {
            IAuth(_authModule).transferOperatorship(newOperatorsData);

            emit OperatorshipTransferred(newOperatorsData);
        }
    }

    function execute(bytes calldata input) external override {
        (bytes memory data, bytes memory proof) = abi.decode(input, (bytes, bytes));

        bytes32 messageHash = ECDSA.toEthSignedMessageHash(keccak256(data));

        // TEST auth and getaway separately
        bool currentOperators = IAuth(_authModule).validateProof(messageHash, proof);

        uint256 chainId;
        bytes32[] memory commandIds;
        string[] memory commands;
        bytes[] memory params;

        try ToposCoreContract(this)._unpackLegacyCommands(data) returns (
            uint256 chainId_,
            bytes32[] memory commandIds_,
            string[] memory commands_,
            bytes[] memory params_
        ) {
            (chainId, commandIds, commands, params) = (chainId_, commandIds_, commands_, params_);
        } catch {
            (chainId, commandIds, commands, params) = abi.decode(data, (uint256, bytes32[], string[], bytes[]));
        }

        if (chainId != block.chainid) revert InvalidChainId();

        uint256 commandsLength = commandIds.length;

        if (commandsLength != commands.length || commandsLength != params.length) revert InvalidCommands();

        for (uint256 i; i < commandsLength; ++i) {
            bytes32 commandId = commandIds[i];

            if (isCommandExecuted(commandId)) continue; /* Ignore if duplicate commandId received */

            bytes4 commandSelector;
            bytes32 commandHash = keccak256(abi.encodePacked(commands[i]));

            if (commandHash == SELECTOR_DEPLOY_TOKEN) {
                commandSelector = ToposCoreContract.deployToken.selector;
            } else if (commandHash == SELECTOR_MINT_TOKEN) {
                commandSelector = ToposCoreContract.mintToken.selector;
            } else if (commandHash == SELECTOR_APPROVE_CONTRACT_CALL) {
                commandSelector = ToposCoreContract.approveContractCall.selector;
            } else if (commandHash == SELECTOR_APPROVE_CONTRACT_CALL_WITH_MINT) {
                commandSelector = ToposCoreContract.approveContractCallWithMint.selector;
            } else if (commandHash == SELECTOR_BURN_TOKEN) {
                commandSelector = ToposCoreContract.burnToken.selector;
            } else if (commandHash == SELECTOR_TRANSFER_OPERATORSHIP) {
                if (!currentOperators) continue;

                commandSelector = ToposCoreContract.transferOperatorship.selector;
            } else {
                continue; /* Ignore if unknown command received */
            }

            // Prevent a re-entrancy from executing this command before it can be marked as successful.
            _setCommandExecuted(commandId, true);
            // solhint-disable-next-line avoid-low-level-calls
            (bool success, ) = address(this).call(abi.encodeWithSelector(commandSelector, params[i], commandId));

            if (success) emit Executed(commandId);
            else _setCommandExecuted(commandId, false);
        }
    }

    /*******************\
    |* Admin Functions *|
    \*******************/

    function setTokenDailyMintLimits(string[] calldata symbols, uint256[] calldata limits) external override onlyAdmin {
        if (symbols.length != limits.length) revert InvalidSetDailyMintLimitsParams();

        for (uint256 i = 0; i < symbols.length; i++) {
            string memory symbol = symbols[i];
            uint256 limit = limits[i];

            if (tokenAddresses(symbol) == address(0)) revert TokenDoesNotExist(symbol);

            _setTokenDailyMintLimit(symbol, limit);
        }
    }

    function upgrade(
        address newImplementation,
        bytes32 newImplementationCodeHash,
        bytes calldata setupParams
    ) external override onlyAdmin {
        if (newImplementationCodeHash != newImplementation.codehash) revert InvalidCodeHash();

        emit Upgraded(newImplementation);

        // AUDIT: If `newImplementation.setup` performs `selfdestruct`, it will result in the loss of _this_ implementation (thereby losing the gateway)
        //        if `upgrade` is entered within the context of _this_ implementation itself.
        if (setupParams.length != 0) {
            // solhint-disable-next-line avoid-low-level-calls
            (bool success, ) = newImplementation.delegatecall(
                abi.encodeWithSelector(IToposCoreContract.setup.selector, setupParams)
            );

            if (!success) revert SetupFailed();
        }

        _setImplementation(newImplementation);
    }

    /******************\
    |* Self Functions *|
    \******************/

    function deployToken(bytes calldata params) external {
        (
            string memory name,
            string memory symbol,
            uint8 decimals,
            uint256 cap,
            address tokenAddress,
            uint256 dailyMintLimit
        ) = abi.decode(params, (string, string, uint8, uint256, address, uint256));

        // Ensure that this symbol has not been taken.
        if (tokenAddresses(symbol) != address(0)) revert TokenAlreadyExists(symbol);

        if (tokenAddress == address(0)) {
            // If token address is no specified, it indicates a request to deploy one.
            bytes32 salt = keccak256(abi.encodePacked(symbol));

            // solhint-disable-next-line avoid-low-level-calls
            (bool success, bytes memory data) = _tokenDeployerImplementation.delegatecall(
                abi.encodeWithSelector(ITokenDeployer.deployToken.selector, name, symbol, decimals, cap, salt)
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

    function mintToken(bytes calldata params, bytes32) external onlySelf {
        (string memory symbol, address account, uint256 amount) = abi.decode(params, (string, address, uint256));

        _mintToken(symbol, account, amount);
    }

    function burnToken(bytes calldata params, bytes32) external onlySelf {
        (string memory symbol, bytes32 salt) = abi.decode(params, (string, bytes32));

        address tokenAddress = tokenAddresses(symbol);

        if (tokenAddress == address(0)) revert TokenDoesNotExist(symbol);

        if (_getTokenType(symbol) == TokenType.External) {
            DepositHandler depositHandler = new DepositHandler{salt: salt}();

            (bool success, bytes memory returnData) = depositHandler.execute(
                tokenAddress,
                abi.encodeWithSelector(
                    IERC20.transfer.selector,
                    address(this),
                    IERC20(tokenAddress).balanceOf(address(depositHandler))
                )
            );

            if (!success || (returnData.length != uint256(0) && !abi.decode(returnData, (bool))))
                revert BurnFailed(symbol);

            // NOTE: `depositHandler` must always be destroyed in the same runtime context that it is deployed.
            depositHandler.destroy(address(this));
        } else {
            IBurnableMintableCappedERC20(tokenAddress).burn(salt);
        }
    }

    function approveContractCall(bytes calldata params, bytes32 commandId) external onlySelf {
        (
            subnetId sourceSubnetId,
            string memory sourceAddress,
            address contractAddress,
            bytes32 payloadHash,
            bytes32 sourceTxHash,
            uint256 sourceEventIndex
        ) = abi.decode(params, (subnetId, string, address, bytes32, bytes32, uint256));

        _setContractCallApproved(commandId, sourceSubnetId, sourceAddress, contractAddress, payloadHash);
        emit ContractCallApproved(
            commandId,
            sourceSubnetId,
            sourceAddress,
            contractAddress,
            payloadHash,
            sourceTxHash,
            sourceEventIndex
        );
    }

    function approveContractCallWithMint(bytes calldata params, bytes32 commandId) external onlySelf {
        (
            subnetId sourceSubnetId,
            string memory sourceAddress,
            address contractAddress,
            bytes32 payloadHash,
            string memory symbol,
            uint256 amount,
            bytes32 sourceTxHash,
            uint256 sourceEventIndex
        ) = abi.decode(params, (subnetId, string, address, bytes32, string, uint256, bytes32, uint256));

        _setContractCallApprovedWithMint(
            commandId,
            sourceSubnetId,
            sourceAddress,
            contractAddress,
            payloadHash,
            symbol,
            amount
        );
        emit ContractCallApprovedWithMint(
            commandId,
            sourceSubnetId,
            sourceAddress,
            contractAddress,
            payloadHash,
            symbol,
            amount,
            sourceTxHash,
            sourceEventIndex
        );
    }

    function transferOperatorship(bytes calldata newOperatorsData, bytes32) external onlySelf {
        IAuth(_authModule).transferOperatorship(newOperatorsData);

        emit OperatorshipTransferred(newOperatorsData);
    }

    /******************\
    |* Public Methods *|
    \******************/

    function sendToken(
        subnetId destinationSubnetId,
        string calldata destinationAddress,
        string calldata symbol,
        uint256 amount
    ) external {
        _burnTokenFrom(msg.sender, symbol, amount);
        emit TokenSent(msg.sender, destinationSubnetId, destinationAddress, symbol, amount);
    }

    function callContract(
        subnetId destinationSubnetId,
        string calldata destinationContractAddress,
        bytes calldata payload
    ) external {
        emit ContractCall(msg.sender, destinationSubnetId, destinationContractAddress, keccak256(payload), payload);
    }

    function callContractWithToken(
        subnetId destinationSubnetId,
        string calldata destinationContractAddress,
        bytes calldata payload,
        string calldata symbol,
        uint256 amount
    ) external {
        _burnTokenFrom(msg.sender, symbol, amount);
        emit ContractCallWithToken(
            msg.sender,
            destinationSubnetId,
            destinationContractAddress,
            keccak256(payload),
            payload,
            symbol,
            amount
        );
    }

    function validateContractCall(
        bytes32 commandId,
        subnetId sourceSubnetId,
        string calldata sourceAddress,
        bytes32 payloadHash
    ) external override returns (bool valid) {
        bytes32 key = _getIsContractCallApprovedKey(commandId, sourceSubnetId, sourceAddress, msg.sender, payloadHash);
        valid = getBool(key);
        if (valid) _setBool(key, false);
    }

    function validateContractCallAndMint(
        bytes32 commandId,
        subnetId sourceSubnetId,
        string calldata sourceAddress,
        bytes32 payloadHash,
        string calldata symbol,
        uint256 amount
    ) external override returns (bool valid) {
        bytes32 key = _getIsContractCallApprovedWithMintKey(
            commandId,
            sourceSubnetId,
            sourceAddress,
            msg.sender,
            payloadHash,
            symbol,
            amount
        );
        valid = getBool(key);
        if (valid) {
            // Prevent re-entrancy
            _setBool(key, false);
            _mintToken(symbol, msg.sender, amount);
        }
    }

    function isContractCallApproved(
        bytes32 commandId,
        subnetId sourceSubnetId,
        string calldata sourceAddress,
        address contractAddress,
        bytes32 payloadHash
    ) external view override returns (bool) {
        return
            getBool(
                _getIsContractCallApprovedKey(commandId, sourceSubnetId, sourceAddress, contractAddress, payloadHash)
            );
    }

    function isContractCallAndMintApproved(
        bytes32 commandId,
        subnetId sourceSubnetId,
        string calldata sourceAddress,
        address contractAddress,
        bytes32 payloadHash,
        string calldata symbol,
        uint256 amount
    ) external view override returns (bool) {
        return
            getBool(
                _getIsContractCallApprovedWithMintKey(
                    commandId,
                    sourceSubnetId,
                    sourceAddress,
                    contractAddress,
                    payloadHash,
                    symbol,
                    amount
                )
            );
    }

    /***********\
    |* Getters *|
    \***********/

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

    /********************\
    |* Internal Methods *|
    \********************/

    function _unpackLegacyCommands(bytes memory executeData)
        external
        pure
        returns (
            uint256 chainId,
            bytes32[] memory commandIds,
            string[] memory commands,
            bytes[] memory params
        )
    {
        (chainId, , commandIds, commands, params) = abi.decode(
            executeData,
            (uint256, uint256, bytes32[], string[], bytes[])
        );
    }

    /***********\
    |* Getters *|
    \***********/

    function allTokensFrozen() external pure override returns (bool) {
        return false;
    }

    function tokenFrozen(string memory) external pure override returns (bool) {
        return false;
    }

    function tokenDailyMintLimit(string memory symbol) public view override returns (uint256) {
        return getUint(_getTokenDailyMintLimitKey(symbol));
    }

    function tokenDailyMintAmount(string memory symbol) public view override returns (uint256) {
        return getUint(_getTokenDailyMintAmountKey(symbol, block.timestamp / 1 days));
    }

    function implementation() public view override returns (address) {
        return getAddress(KEY_IMPLEMENTATION);
    }

    function tokenAddresses(string memory symbol) public view override returns (address) {
        return getAddress(_getTokenAddressKey(symbol));
    }

    function isCommandExecuted(bytes32 commandId) public view override returns (bool) {
        return getBool(_getIsCommandExecutedKey(commandId));
    }

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
        address tokenAddress = tokenAddresses(symbol);

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
        address tokenAddress = tokenAddresses(symbol);

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

            return;
        }

        if (tokenType == TokenType.InternalBurnableFrom) {
            burnSuccess = _callERC20Token(
                tokenAddress,
                abi.encodeWithSelector(IBurnableMintableCappedERC20.burnFrom.selector, sender, amount)
            );

            if (!burnSuccess) revert BurnFailed(symbol);

            return;
        }

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
        _setAddress(_getTokenAddressKey(symbol), tokenAddress);
    }

    function _setCommandExecuted(bytes32 commandId, bool executed) internal {
        _setBool(_getIsCommandExecutedKey(commandId), executed);
    }

    function _setContractCallApproved(
        bytes32 commandId,
        subnetId sourceSubnetId,
        string memory sourceAddress,
        address contractAddress,
        bytes32 payloadHash
    ) internal {
        _setBool(
            _getIsContractCallApprovedKey(commandId, sourceSubnetId, sourceAddress, contractAddress, payloadHash),
            true
        );
    }

    function _setContractCallApprovedWithMint(
        bytes32 commandId,
        subnetId sourceSubnetId,
        string memory sourceAddress,
        address contractAddress,
        bytes32 payloadHash,
        string memory symbol,
        uint256 amount
    ) internal {
        _setBool(
            _getIsContractCallApprovedWithMintKey(
                commandId,
                sourceSubnetId,
                sourceAddress,
                contractAddress,
                payloadHash,
                symbol,
                amount
            ),
            true
        );
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

    function _getTokenAddressKey(string memory symbol) internal pure returns (bytes32) {
        return keccak256(abi.encodePacked(PREFIX_TOKEN_ADDRESS, symbol));
    }

    function _getIsCommandExecutedKey(bytes32 commandId) internal pure returns (bytes32) {
        return keccak256(abi.encodePacked(PREFIX_COMMAND_EXECUTED, commandId));
    }

    /********************\
    |* Internal Methods *|
    \********************/

    function _getIsContractCallApprovedKey(
        bytes32 commandId,
        subnetId sourceSubnetId,
        string memory sourceAddress,
        address contractAddress,
        bytes32 payloadHash
    ) internal pure returns (bytes32) {
        return
            keccak256(
                abi.encode(
                    PREFIX_CONTRACT_CALL_APPROVED,
                    commandId,
                    sourceSubnetId,
                    sourceAddress,
                    contractAddress,
                    payloadHash
                )
            );
    }

    function _getIsContractCallApprovedWithMintKey(
        bytes32 commandId,
        subnetId sourceSubnetId,
        string memory sourceAddress,
        address contractAddress,
        bytes32 payloadHash,
        string memory symbol,
        uint256 amount
    ) internal pure returns (bytes32) {
        return
            keccak256(
                abi.encode(
                    PREFIX_CONTRACT_CALL_APPROVED_WITH_MINT,
                    commandId,
                    sourceSubnetId,
                    sourceAddress,
                    contractAddress,
                    payloadHash,
                    symbol,
                    amount
                )
            );
    }
}