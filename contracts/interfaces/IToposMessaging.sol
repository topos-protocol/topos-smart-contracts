// SPDX-License-Identifier: MIT
pragma solidity ^0.8.9;

import "solidity-rlp/contracts/RLPReader.sol";
import {SubnetId} from "./IToposCore.sol";

interface IToposMessaging {
    struct Proof {
        uint256 kind;
        bytes rlpTxIndex;
        uint256 txIndex;
        bytes mptKey;
        RLPReader.RLPItem[] stack;
    }

    struct Token {
        string symbol;
        address tokenAddress;
    }

    enum TokenType {
        InternalBurnable,
        InternalBurnableFrom,
        External
    }

    event TokenDailyMintLimitUpdated(string symbol, uint256 limit);

    event TokenDeployed(string symbol, address tokenAddress);

    event TokenSent(
        address indexed sender,
        SubnetId sourceSubnetId,
        SubnetId targetSubnetId,
        address receiver,
        string symbol,
        uint256 amount
    );

    error BurnFailed(string symbol);
    error CertNotPresent();
    error ExceedDailyMintLimit(string symbol);
    error IllegalMemoryAccess();
    error InvalidAmount();
    error InvalidMerkleProof();
    error InvalidSetDailyMintLimitsParams();
    error InvalidSubnetId();
    error InvalidTokenDeployer();
    error InvalidToposCore();
    error MintFailed(string symbol);
    error TokenAlreadyExists(string symbol);
    error TokenContractDoesNotExist(address token);
    error TokenDeployFailed(string symbol);
    error TokenDoesNotExist(string symbol);
    error TransferAlreadyExecuted();
    error UnsupportedProofKind();

    function deployToken(bytes calldata params) external;

    function executeAssetTransfer(
        uint256 indexOfDataInTxRaw,
        bytes memory proofBlob,
        bytes calldata txRaw,
        bytes32 txRoot
    ) external;

    //TODO: decide what to do with this function
    function giveToken(string memory symbol, address account, uint256 amount) external;

    function sendToken(SubnetId targetSubnetId, address receiver, string calldata symbol, uint256 amount) external;

    // TODO: decide what to do with this function
    // function setTokenDailyMintLimits(string[] calldata symbols, uint256[] calldata limits) external;

    function validateMerkleProof(bytes memory proofBlob, bytes32 txHash, bytes32 txRoot) external returns (bool);

    function getTokenBySymbol(string memory symbol) external view returns (Token memory);

    function getTokenCount() external view returns (uint256);

    function getTokenKeyAtIndex(uint256 index) external view returns (bytes32);

    function toposCore() external view returns (address);

    function tokens(bytes32 tokenKey) external view returns (string memory, address);

    function tokenDailyMintAmount(string memory symbol) external view returns (uint256);

    function tokenDailyMintLimit(string memory symbol) external view returns (uint256);

    function tokenDeployer() external view returns (address);
}
