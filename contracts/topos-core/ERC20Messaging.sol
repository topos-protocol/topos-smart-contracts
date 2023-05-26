// SPDX-License-Identifier: MIT
pragma solidity ^0.8.9;

import "./Bytes32Sets.sol";

import "./../interfaces/IERC20Messaging.sol";
import "./../interfaces/ITokenDeployer.sol";

import {IBurnableMintableCappedERC20} from "./../interfaces/IBurnableMintableCappedERC20.sol";
import {ToposMessaging} from "./ToposMessaging.sol";

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

contract ERC20Messaging is IERC20Messaging, ToposMessaging {
    using Bytes32SetsLib for Bytes32SetsLib.Set;

    // Slot names should be prefixed with some standard string
    bytes32 internal constant PREFIX_TOKEN_KEY = keccak256("token-key");
    bytes32 internal constant PREFIX_TOKEN_TYPE = keccak256("token-type");
    bytes32 internal constant PREFIX_TOKEN_DAILY_MINT_LIMIT = keccak256("token-daily-mint-limit");
    bytes32 internal constant PREFIX_TOKEN_DAILY_MINT_AMOUNT = keccak256("token-daily-mint-amount");

    /// @notice Set of Token Keys derived from token symbols
    Bytes32SetsLib.Set tokenSet;

    /// @notice Internal token deployer (ERCBurnableMintable by default)
    address internal immutable _tokenDeployerAddr;

    /// @notice Mapping to store Tokens
    mapping(bytes32 => Token) public tokens;

    /// @notice Constructor for ERC20Messaging contract
    /// @param tokenDeployerAddr Address of the token deployer contract
    constructor(address tokenDeployerAddr, address toposCoreAddr) ToposMessaging(toposCoreAddr) {
        if (tokenDeployerAddr.code.length == uint256(0)) revert InvalidTokenDeployer();
        _tokenDeployerAddr = tokenDeployerAddr;
    }

    /// @notice Deploy/register a token
    /// @param params Encoded token params for deploying/registering a token
    function deployToken(bytes calldata params) external {
        (
            string memory name,
            string memory symbol,
            uint256 cap,
            address tokenAddress,
            uint256 dailyMintLimit,
            uint256 initialSupply
        ) = abi.decode(params, (string, string, uint256, address, uint256, uint256));

        // Ensure that this token does not exist already.
        bytes32 tokenKey = _getTokenKey(tokenAddress);
        if (tokenSet.exists(tokenKey)) revert TokenAlreadyExists(tokenAddress);

        if (tokenAddress == address(0)) {
            // If token address is no specified, it indicates a request to deploy one.
            bytes32 salt = keccak256(abi.encodePacked(msg.sender, symbol));

            // slither-disable-start reentrancy-no-eth
            // solhint-disable-next-line avoid-low-level-calls
            (bool success, bytes memory data) = _tokenDeployerAddr.delegatecall(
                abi.encodeWithSelector(
                    ITokenDeployer.deployToken.selector,
                    name,
                    symbol,
                    cap,
                    initialSupply,
                    msg.sender,
                    address(this),
                    salt
                )
            );
            // slither-disable-end reentrancy-no-eth

            if (!success) revert TokenDeployFailed();

            tokenAddress = abi.decode(data, (address));

            _setTokenType(tokenAddress, TokenType.InternalBurnableFrom);
        } else {
            revert UnsupportedTokenType();
            // _setTokenType(tokenAddress, TokenType.External);
        }

        _setTokenAddress(symbol, tokenAddress);
        _setTokenDailyMintLimit(dailyMintLimit, tokenAddress);

        emit TokenDeployed(symbol, tokenAddress);
    }

    /// @notice Entry point for sending a cross-subnet asset transfer
    /// @dev The input data is sent to the target subnet externally
    /// @param targetSubnetId Target subnet ID
    /// @param /*receiver*/ Receiver's address (avoiding unused local variable warning)
    /// @param tokenAddress Address of target token contract
    /// @param amount Amount of token to send
    function sendToken(SubnetId targetSubnetId, address /*receiver*/, address tokenAddress, uint256 amount) external {
        if (_toposCoreAddr.code.length == uint256(0)) revert InvalidToposCore();
        _burnTokenFrom(msg.sender, tokenAddress, amount);
        _emitMessageSentEvent(targetSubnetId);
    }

    /// @notice Gets the token by address
    /// @param tokenAddress Address of token contract
    function getTokenByAddress(address tokenAddress) public view returns (Token memory token) {
        bytes32 tokenKey = _getTokenKey(tokenAddress);
        token = tokens[tokenKey];
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
    /// @param tokenAddress Address of token contract
    function tokenDailyMintAmount(address tokenAddress) public view returns (uint256) {
        return getUint(_getTokenDailyMintAmountKey(tokenAddress, block.timestamp / 1 days));
    }

    /// @notice Get the token daily mint limit
    /// @param tokenAddress Address of token contract
    function tokenDailyMintLimit(address tokenAddress) public view returns (uint256) {
        return getUint(_getTokenDailyMintLimitKey(tokenAddress));
    }

    /// @notice Get the address of token deployer contract
    function tokenDeployer() public view returns (address) {
        return _tokenDeployerAddr;
    }

    /// @notice Execute a cross-subnet asset transfer
    /// @param indexOfDataInTxRaw Index of data in txRaw
    /// @param txRaw Raw transaction data
    function _execute(uint256 indexOfDataInTxRaw, bytes calldata txRaw) internal override {
        (SubnetId targetSubnetId, address receiver, address tokenAddress, uint256 amount) = abi.decode(
            txRaw[indexOfDataInTxRaw + 4:], // omit the 4 bytes function selector
            (SubnetId, address, address, uint256)
        );
        if (!_validateTargetSubnetId(targetSubnetId)) revert InvalidSubnetId();

        // prevent reentrancy
        _mintToken(tokenAddress, receiver, amount);
    }

    /// @notice Burn token internally
    /// @param sender Account to burn token from
    /// @param tokenAddress Address of target token contract
    /// @param amount Amount of token to burn
    function _burnTokenFrom(address sender, address tokenAddress, uint256 amount) internal {
        bytes32 tokenKey = _getTokenKey(tokenAddress);
        if (!tokenSet.exists(tokenKey)) revert TokenDoesNotExist(tokenAddress);
        if (amount == 0) revert InvalidAmount();

        TokenType tokenType = _getTokenType(tokenAddress);
        bool burnSuccess;

        if (tokenType == TokenType.External) {
            revert UnsupportedTokenType();
        } else {
            burnSuccess = _callERC20Token(
                tokenAddress,
                abi.encodeWithSelector(IBurnableMintableCappedERC20.burnFrom.selector, sender, amount)
            );
            if (!burnSuccess) revert BurnFailed(tokenAddress);
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
    /// @param tokenAddress Address of token contract
    /// @param account Account to mint token to
    /// @param amount Amount of token to mint
    function _mintToken(address tokenAddress, address account, uint256 amount) internal {
        bytes32 tokenKey = _getTokenKey(tokenAddress);
        if (!tokenSet.exists(tokenKey)) revert TokenDoesNotExist(tokenAddress);

        _setTokenDailyMintAmount(tokenAddress, tokenDailyMintAmount(tokenAddress) + amount);

        if (_getTokenType(tokenAddress) == TokenType.External) {
            revert UnsupportedTokenType();
        } else {
            IBurnableMintableCappedERC20(tokenAddress).mint(account, amount);
        }
    }

    /// @notice Store the token address for the specified symbol
    /// @param symbol Symbol of token
    /// @param tokenAddress Address of token contract
    function _setTokenAddress(string memory symbol, address tokenAddress) internal {
        bytes32 tokenKey = _getTokenKey(tokenAddress);
        tokenSet.insert(tokenKey);
        Token storage token = tokens[tokenKey];
        token.symbol = symbol;
        token.addr = tokenAddress;
    }

    /// @notice Set the token daily mint limit for a token address
    /// @param limit Daily mint limit of token
    /// @param tokenAddress Address of token contract
    function _setTokenDailyMintLimit(uint256 limit, address tokenAddress) internal {
        _setUint(_getTokenDailyMintLimitKey(tokenAddress), limit);

        emit TokenDailyMintLimitUpdated(tokenAddress, limit);
    }

    /// @notice Set the token daily mint amount for a token address
    /// @param tokenAddress Address of token contract
    /// @param amount Daily mint amount of token
    function _setTokenDailyMintAmount(address tokenAddress, uint256 amount) internal {
        uint256 limit = tokenDailyMintLimit(tokenAddress);
        if (limit > 0 && amount > limit) revert ExceedDailyMintLimit(tokenAddress);

        _setUint(_getTokenDailyMintAmountKey(tokenAddress, block.timestamp / 1 days), amount);
    }

    /// @notice Set the token type for a token address
    /// @param tokenAddress Address of token contract
    /// @param tokenType Type of token (external/internal)
    function _setTokenType(address tokenAddress, TokenType tokenType) internal {
        _setUint(_getTokenTypeKey(tokenAddress), uint256(tokenType));
    }

    /// @notice Get the token type for a token address
    /// @param tokenAddress Address of token contract
    function _getTokenType(address tokenAddress) internal view returns (TokenType) {
        return TokenType(getUint(_getTokenTypeKey(tokenAddress)));
    }

    /// @notice Get the key for the token daily mint limit
    /// @param tokenAddress Address of token contract
    function _getTokenDailyMintLimitKey(address tokenAddress) internal pure returns (bytes32) {
        return keccak256(abi.encodePacked(PREFIX_TOKEN_DAILY_MINT_LIMIT, tokenAddress));
    }

    /// @notice Get the key for the token daily mint amount
    /// @param tokenAddress Address of token contract
    /// @param day Day of token daily mint amount
    function _getTokenDailyMintAmountKey(address tokenAddress, uint256 day) internal pure returns (bytes32) {
        return keccak256(abi.encodePacked(PREFIX_TOKEN_DAILY_MINT_AMOUNT, tokenAddress, day));
    }

    /// @notice Get the key for the token type
    /// @param tokenAddress Address of token contract
    function _getTokenTypeKey(address tokenAddress) internal pure returns (bytes32) {
        return keccak256(abi.encodePacked(PREFIX_TOKEN_TYPE, tokenAddress));
    }

    /// @notice Get the key for the token
    /// @param tokenAddress Address of token contract
    function _getTokenKey(address tokenAddress) internal pure returns (bytes32) {
        return keccak256(abi.encodePacked(PREFIX_TOKEN_KEY, tokenAddress));
    }
}
