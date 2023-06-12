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

    error CertNotPresent();
    error IllegalMemoryAccess();
    error InvalidMerkleProof();
    error InvalidSubnetId();
    error InvalidToposCore();
    error TransactionAlreadyExecuted();
    error UnsupportedProofKind();

    function validateMerkleProof(bytes memory proofBlob, bytes32 txHash, bytes32 txRoot) external returns (bool);

    function toposCore() external view returns (address);
}
