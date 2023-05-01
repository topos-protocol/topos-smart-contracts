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
        address addr;
    }

    enum TokenType {
        InternalBurnableFrom,
        External // Not supported yet
    }

    event TokenDailyMintLimitUpdated(address tokenAddress, uint256 limit);

    event TokenDeployed(string symbol, address tokenAddress);

    event TokenSent(
        address indexed sender,
        SubnetId sourceSubnetId,
        SubnetId targetSubnetId,
        address receiver,
        address tokenAddress,
        uint256 amount
    );

    error BurnFailed(address tokenAddress);
    error CertNotPresent();
    error ExceedDailyMintLimit(address tokenAddress);
    error IllegalMemoryAccess();
    error InvalidAmount();
    error InvalidMerkleProof();
    error InvalidSetDailyMintLimitsParams();
    error InvalidSubnetId();
    error InvalidTokenDeployer();
    error InvalidToposCore();
    error TokenAlreadyExists(address tokenAddress);
    error TokenDeployFailed();
    error TokenDoesNotExist(address tokenAddress);
    error TransferAlreadyExecuted();
    error UnsupportedProofKind();
    error UnsupportedTokenType();

    function deployToken(bytes calldata params) external;

    function executeAssetTransfer(
        uint256 indexOfDataInTxRaw,
        bytes memory proofBlob,
        bytes calldata txRaw,
        bytes32 txRoot
    ) external;

    function sendToken(SubnetId targetSubnetId, address receiver, address tokenAddress, uint256 amount) external;

    function validateMerkleProof(bytes memory proofBlob, bytes32 txHash, bytes32 txRoot) external returns (bool);

    function getTokenByAddress(address tokenAddress) external view returns (Token memory token);

    function getTokenCount() external view returns (uint256);

    function getTokenKeyAtIndex(uint256 index) external view returns (bytes32);

    function toposCore() external view returns (address);

    function tokens(bytes32 tokenKey) external view returns (string memory, address);

    function tokenDailyMintAmount(address tokenAddress) external view returns (uint256);

    function tokenDailyMintLimit(address tokenAddress) external view returns (uint256);

    function tokenDeployer() external view returns (address);
}
