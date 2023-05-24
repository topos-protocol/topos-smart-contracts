// SPDX-License-Identifier: MIT
pragma solidity ^0.8.9;

import {IToposMessaging, SubnetId} from "./IToposMessaging.sol";

interface IERC20Messaging is IToposMessaging {
    struct Token {
        string symbol;
        address addr;
    }

    enum TokenType {
        InternalBurnableFrom,
        External // Not supported yet
    }

    event TokenDailyMintLimitUpdated(address tokenAddress, uint256 limit);

    event TokenDeployed(string symbol, address tokenAddress);

    error BurnFailed(address tokenAddress);
    error ExceedDailyMintLimit(address tokenAddress);
    error InvalidAmount();
    error InvalidSetDailyMintLimitsParams();
    error InvalidTokenDeployer();
    error TokenAlreadyExists(address tokenAddress);
    error TokenDeployFailed();
    error TokenDoesNotExist(address tokenAddress);
    error UnsupportedTokenType();

    function deployToken(bytes calldata params) external;

    function sendToken(SubnetId targetSubnetId, address receiver, address tokenAddress, uint256 amount) external;

    function getTokenByAddress(address tokenAddress) external view returns (Token memory token);

    function getTokenCount() external view returns (uint256);

    function getTokenKeyAtIndex(uint256 index) external view returns (bytes32);

    function tokens(bytes32 tokenKey) external view returns (string memory, address);

    function tokenDailyMintAmount(address tokenAddress) external view returns (uint256);

    function tokenDailyMintLimit(address tokenAddress) external view returns (uint256);

    function tokenDeployer() external view returns (address);
}
