// SPDX-License-Identifier: MIT
pragma solidity ^0.8.9;

import "./Bytes32Sets.sol";
import "./EternalStorage.sol";

import "./../interfaces/IToposMessaging.sol";
import "./../interfaces/IToposCore.sol";
import "./../interfaces/ITokenDeployer.sol";

import {IBurnableMintableCappedERC20} from "./../interfaces/IBurnableMintableCappedERC20.sol";
import {MerklePatriciaProofVerifier} from "./MerklePatriciaProofVerifier.sol";

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

contract ToposMessaging is IToposMessaging, EternalStorage {
    using Bytes32SetsLib for Bytes32SetsLib.Set;
    using RLPReader for RLPReader.RLPItem;
    using RLPReader for bytes;

    // Slot names should be prefixed with some standard string
    bytes32 internal constant PREFIX_TOKEN_KEY = keccak256("token-key");
    bytes32 internal constant PREFIX_TOKEN_TYPE = keccak256("token-type");
    bytes32 internal constant PREFIX_SEND_TOKEN_EXECUTED = keccak256("send-token-executed");
    bytes32 internal constant PREFIX_TOKEN_DAILY_MINT_LIMIT = keccak256("token-daily-mint-limit");
    bytes32 internal constant PREFIX_TOKEN_DAILY_MINT_AMOUNT = keccak256("token-daily-mint-amount");

    /// @notice Set of Token Keys derived from token symbols
    Bytes32SetsLib.Set tokenSet;

    /// @notice Internal topos core address
    address internal immutable _toposCoreAddr;

    /// @notice Internal token deployer (ERCBurnableMintable by default)
    address internal immutable _tokenDeployerAddr;

    /// @notice Mapping to store Tokens
    mapping(bytes32 => Token) public tokens;

    /// @notice Constructor for ToposMessaging contract
    /// @param tokenDeployerAddr Address of token deployer
    /// @param toposCoreAddr Address of topos core
    constructor(address tokenDeployerAddr, address toposCoreAddr) {
        if (tokenDeployerAddr.code.length == uint256(0)) revert InvalidTokenDeployer();
        if (toposCoreAddr.code.length == uint256(0)) revert InvalidToposCore();
        _tokenDeployerAddr = tokenDeployerAddr;
        _toposCoreAddr = toposCoreAddr;
    }

    /// @notice Deploy/register a token
    /// @param params Encoded token params for deploying/registering a token
    function deployToken(bytes calldata params) external {
        (string memory name, string memory symbol, uint256 cap, address tokenAddress, uint256 dailyMintLimit) = abi
            .decode(params, (string, string, uint256, address, uint256));

        // Ensure that this symbol has not been taken.
        if (getTokenBySymbol(symbol).tokenAddress != address(0)) revert TokenAlreadyExists(symbol);

        if (tokenAddress == address(0)) {
            // If token address is no specified, it indicates a request to deploy one.
            bytes32 salt = keccak256(abi.encodePacked(symbol));

            // slither-disable-start reentrancy-no-eth
            // solhint-disable-next-line avoid-low-level-calls
            (bool success, bytes memory data) = _tokenDeployerAddr.delegatecall(
                abi.encodeWithSelector(ITokenDeployer.deployToken.selector, name, symbol, cap, salt)
            );
            // slither-disable-end reentrancy-no-eth

            if (!success) revert TokenDeployFailed(symbol);

            tokenAddress = abi.decode(data, (address));

            _setTokenType(symbol, TokenType.InternalBurnableFrom);
        } else {
            revert UnsupportedTokenType();
            // _setTokenType(symbol, TokenType.External);
        }

        _setTokenAddress(symbol, tokenAddress);
        _setTokenDailyMintLimit(symbol, dailyMintLimit);

        emit TokenDeployed(symbol, tokenAddress);
    }

    /// @notice Entry point for executing asset transfer
    /// @param indexOfDataInTxRaw Index of tx.data in raw transaction hex
    /// @param txRaw RLP encoded raw transaction hex
    /// @param proofBlob RLP encoded proof blob
    /// @param txRoot Transactions root
    function executeAssetTransfer(
        uint256 indexOfDataInTxRaw,
        bytes memory proofBlob,
        bytes calldata txRaw,
        bytes32 txRoot
    ) external {
        if (_toposCoreAddr.code.length == uint256(0)) revert InvalidToposCore();

        if (txRaw.length < indexOfDataInTxRaw + 4) revert IllegalMemoryAccess();

        CertificateId certId = IToposCore(_toposCoreAddr).txRootToCertId(txRoot);
        if (!IToposCore(_toposCoreAddr).certificateExists(certId)) revert CertNotPresent();

        // In order to validate the transaction pass the entire transaction bytes which is then hashed.
        // The transaction hash is used as a leaf to validate the inclusion proof.
        bytes32 txHash = keccak256(abi.encodePacked(txRaw));
        if (!validateMerkleProof(proofBlob, txHash, txRoot)) revert InvalidMerkleProof();
        (SubnetId targetSubnetId, address receiver, string memory symbol, uint256 amount) = abi.decode(
            txRaw[indexOfDataInTxRaw + 4:], // omit the 4 bytes function selector
            (SubnetId, address, string, uint256)
        );
        SubnetId toposCoreSubnetId = IToposCore(_toposCoreAddr).networkSubnetId();
        if (SubnetId.unwrap(targetSubnetId) != SubnetId.unwrap(toposCoreSubnetId)) revert InvalidSubnetId();

        if (_isSendTokenExecuted(txHash)) revert TransferAlreadyExecuted();

        // prevent re-entrancy
        _setSendTokenExecuted(txHash);
        _mintToken(symbol, receiver, amount);
    }

    // TODO: decide what to do with this function
    /// @dev Give token to an account for testing
    function giveToken(string memory symbol, address account, uint256 amount) external {
        _mintToken(symbol, account, amount);
    }

    /// @notice Entry point for sending a cross-subnet asset transfer
    /// @param targetSubnetId Target subnet ID
    /// @param receiver Receiver's address
    /// @param symbol Token symbol
    /// @param amount Amount of token to send
    function sendToken(SubnetId targetSubnetId, address receiver, string calldata symbol, uint256 amount) external {
        if (_toposCoreAddr.code.length == uint256(0)) revert InvalidToposCore();
        _burnTokenFrom(msg.sender, symbol, amount);
        emit TokenSent(
            msg.sender,
            IToposCore(_toposCoreAddr).networkSubnetId(),
            targetSubnetId,
            receiver,
            symbol,
            amount
        );
    }

    // TODO: decide what to do with this function
    /// @notice Set token daily mint limit
    /// @param symbols Symbols of tokens
    /// @param limits Daily mint limits of tokens
    // function setTokenDailyMintLimits(
    //     string[] calldata symbols,
    //     uint256[] calldata limits
    // ) external override {
    //     if (symbols.length != limits.length) revert InvalidSetDailyMintLimitsParams();

    //     for (uint256 i = 0; i < symbols.length; i++) {
    //         string memory symbol = symbols[i];
    //         uint256 limit = limits[i];

    //         if (getTokenBySymbol(symbol).tokenAddress == address(0)) revert TokenDoesNotExist(symbol);

    //         _setTokenDailyMintLimit(symbol, limit);
    //     }
    // }

    /// @notice Get the token by symbol
    /// @param symbol Symbol of token
    function getTokenBySymbol(string memory symbol) public view returns (Token memory) {
        bytes32 tokenKey = _getTokenKey(symbol);
        return tokens[tokenKey];
    }

    /// @notice Get the number of tokens deployed/registered
    function getTokenCount() public view returns (uint256) {
        return tokenSet.count();
    }

    /// @notice Get the token key at the specified index
    /// @param index Index of token key
    function getTokenKeyAtIndex(uint256 index) public view returns (bytes32) {
        return tokenSet.keyAtIndex(index);
    }

    /// @notice Get the token daily mint amount
    /// @param symbol Symbol of token
    function tokenDailyMintAmount(string memory symbol) public view returns (uint256) {
        return getUint(_getTokenDailyMintAmountKey(symbol, block.timestamp / 1 days));
    }

    /// @notice Get the token daily mint limit
    /// @param symbol Symbol of token
    function tokenDailyMintLimit(string memory symbol) public view returns (uint256) {
        return getUint(_getTokenDailyMintLimitKey(symbol));
    }

    /// @notice Get the address of token deployer contract
    function tokenDeployer() public view returns (address) {
        return _tokenDeployerAddr;
    }

    /// @notice Get the address of topos core contract
    function toposCore() public view returns (address) {
        return _toposCoreAddr;
    }

    /// @notice Validate a Merkle proof for an external transaction
    /// @param proofBlob RLP encoded proof blob
    /// @param txHash Transaction hash
    /// @param txRoot Transactions root
    function validateMerkleProof(
        bytes memory proofBlob,
        bytes32 txHash,
        bytes32 txRoot
    ) public pure override returns (bool) {
        Proof memory proof = _decodeProofBlob(proofBlob);

        if (proof.kind != 1) revert UnsupportedProofKind();

        bytes memory txRawFromProof = MerklePatriciaProofVerifier.extractProofValue(txRoot, proof.mptKey, proof.stack);
        if (txRawFromProof.length == 0) {
            // Empty return value for proof of exclusion
            return false;
        } else {
            bytes32 txHashFromProof = keccak256(abi.encodePacked(txRawFromProof));
            return txHash == txHashFromProof;
        }
    }

    /// @notice Burn token internally
    /// @param sender Account to burn token from
    /// @param symbol Symbol of token
    /// @param amount Amount of token to burn
    function _burnTokenFrom(address sender, string memory symbol, uint256 amount) internal {
        address tokenAddress = getTokenBySymbol(symbol).tokenAddress;

        if (tokenAddress == address(0)) revert TokenDoesNotExist(symbol);
        if (amount == 0) revert InvalidAmount();

        TokenType tokenType = _getTokenType(symbol);
        bool burnSuccess;

        if (tokenType == TokenType.External) {
            revert UnsupportedTokenType();
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

    /// @notice Low level call to external token contract
    /// @dev Sends a low-level call to the token contract
    /// @param tokenAddress Address of token contract
    /// @param callData Data to call
    function _callERC20Token(address tokenAddress, bytes memory callData) internal returns (bool) {
        // solhint-disable-next-line avoid-low-level-calls
        (bool success, bytes memory returnData) = tokenAddress.call(callData);
        return success && (returnData.length == uint256(0) || abi.decode(returnData, (bool)));
    }

    /// @notice Mint token internally
    /// @param symbol Symbol of token
    /// @param account Account to mint token to
    /// @param amount Amount of token to mint
    function _mintToken(string memory symbol, address account, uint256 amount) internal {
        address tokenAddress = getTokenBySymbol(symbol).tokenAddress;

        if (tokenAddress == address(0)) revert TokenDoesNotExist(symbol);

        _setTokenDailyMintAmount(symbol, tokenDailyMintAmount(symbol) + amount);

        if (_getTokenType(symbol) == TokenType.External) {
            revert UnsupportedTokenType();
        } else {
            IBurnableMintableCappedERC20(tokenAddress).mint(account, amount);
        }
    }

    /// @notice Set a flag to indicate that the asset transfer transaction has been executed
    /// @param txHash Hash of asset transfer transaction
    function _setSendTokenExecuted(bytes32 txHash) internal {
        _setBool(_getIsSendTokenExecutedKey(txHash), true);
    }

    /// @notice Set the token address for the specified symbol
    /// @param symbol Symbol of token
    /// @param tokenAddress Address of token contract
    function _setTokenAddress(string memory symbol, address tokenAddress) internal {
        bytes32 tokenKey = _getTokenKey(symbol);
        tokenSet.insert(tokenKey);
        Token storage token = tokens[tokenKey];
        token.symbol = symbol;
        token.tokenAddress = tokenAddress;
    }

    /// @notice Set the token daily mint limit for the specified symbol
    /// @param symbol Symbol of token
    /// @param limit Daily mint limit of token
    function _setTokenDailyMintLimit(string memory symbol, uint256 limit) internal {
        _setUint(_getTokenDailyMintLimitKey(symbol), limit);

        emit TokenDailyMintLimitUpdated(symbol, limit);
    }

    /// @notice Set the token daily mint amount for the specified symbol
    /// @param symbol Symbol of token
    /// @param amount Daily mint amount of token
    function _setTokenDailyMintAmount(string memory symbol, uint256 amount) internal {
        uint256 limit = tokenDailyMintLimit(symbol);
        if (limit > 0 && amount > limit) revert ExceedDailyMintLimit(symbol);

        _setUint(_getTokenDailyMintAmountKey(symbol, block.timestamp / 1 days), amount);
    }

    /// @notice Set the token type for the specified symbol
    /// @param symbol Symbol of token
    /// @param tokenType Type of token (external/internal)
    function _setTokenType(string memory symbol, TokenType tokenType) internal {
        _setUint(_getTokenTypeKey(symbol), uint256(tokenType));
    }

    /// @notice Get the token type for the specified symbol
    /// @param symbol Symbol of token
    function _getTokenType(string memory symbol) internal view returns (TokenType) {
        return TokenType(getUint(_getTokenTypeKey(symbol)));
    }

    /// @notice Get the flag to indicate that the asset transfer transaction has been executed
    /// @param txHash Hash of asset transfer transaction
    function _isSendTokenExecuted(bytes32 txHash) internal view returns (bool) {
        return getBool(_getIsSendTokenExecutedKey(txHash));
    }

    /// @notice Get the key for the token daily mint limit
    /// @param symbol Symbol of token
    function _getTokenDailyMintLimitKey(string memory symbol) internal pure returns (bytes32) {
        return keccak256(abi.encodePacked(PREFIX_TOKEN_DAILY_MINT_LIMIT, symbol));
    }

    /// @notice Get the key for the token daily mint amount
    /// @param symbol Symbol of token
    /// @param day Day of token daily mint amount
    function _getTokenDailyMintAmountKey(string memory symbol, uint256 day) internal pure returns (bytes32) {
        return keccak256(abi.encodePacked(PREFIX_TOKEN_DAILY_MINT_AMOUNT, symbol, day));
    }

    /// @notice Get the key for the token type
    /// @param symbol Symbol of token
    function _getTokenTypeKey(string memory symbol) internal pure returns (bytes32) {
        return keccak256(abi.encodePacked(PREFIX_TOKEN_TYPE, symbol));
    }

    /// @notice Get the key for the token
    /// @param symbol Symbol of token
    function _getTokenKey(string memory symbol) internal pure returns (bytes32) {
        return keccak256(abi.encodePacked(PREFIX_TOKEN_KEY, symbol));
    }

    /// @notice Get the key for the flag to indicate that the asset transfer transaction has been executed
    /// @param txHash Hash of asset transfer transaction
    function _getIsSendTokenExecutedKey(bytes32 txHash) internal pure returns (bytes32) {
        return keccak256(abi.encode(PREFIX_SEND_TOKEN_EXECUTED, txHash));
    }

    /// @notice Decode the proof blob into Proof struct
    /// @param proofBlob RLP encoded proof blob
    function _decodeProofBlob(bytes memory proofBlob) internal pure returns (Proof memory proof) {
        RLPReader.RLPItem[] memory proofFields = proofBlob.toRlpItem().toList();
        bytes memory rlpTxIndex = proofFields[1].toRlpBytes();
        proof = Proof(
            proofFields[0].toUint(),
            rlpTxIndex,
            proofFields[1].toUint(),
            _decodeNibbles(rlpTxIndex, 0),
            proofFields[2].toList()
        );
    }

    /// @notice Decode the nibbles from the compact bytes
    /// @param compact compact bytes to decode
    function _decodeNibbles(bytes memory compact, uint256 skipNibbles) internal pure returns (bytes memory nibbles) {
        require(compact.length > 0);

        uint256 length = compact.length * 2;
        require(skipNibbles <= length);
        length -= skipNibbles;

        nibbles = new bytes(length);
        uint256 nibblesLength = 0;

        for (uint256 i = skipNibbles; i < skipNibbles + length; i += 1) {
            if (i % 2 == 0) {
                nibbles[nibblesLength] = bytes1((uint8(compact[i / 2]) >> 4) & 0xF);
            } else {
                nibbles[nibblesLength] = bytes1((uint8(compact[i / 2]) >> 0) & 0xF);
            }
            nibblesLength += 1;
        }

        assert(nibblesLength == nibbles.length);
    }
}
