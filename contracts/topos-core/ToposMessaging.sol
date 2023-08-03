// SPDX-License-Identifier: MIT
pragma solidity ^0.8.9;

import "./EternalStorage.sol";

import "./../interfaces/IToposCore.sol";
import "./../interfaces/IToposMessaging.sol";

import {MerklePatriciaProofVerifier} from "./MerklePatriciaProofVerifier.sol";

contract ToposMessaging is IToposMessaging, EternalStorage {
    using RLPReader for RLPReader.RLPItem;
    using RLPReader for bytes;

    // Slot names should be prefixed with some standard string
    bytes32 internal constant PREFIX_EXECUTED = keccak256("executed");

    /// @notice Internal topos core address
    address internal immutable _toposCoreAddr;

    /// @notice Constructor for ToposMessaging contract
    /// @param toposCoreAddr Address of topos core
    constructor(address toposCoreAddr) {
        if (toposCoreAddr.code.length == uint256(0)) revert InvalidToposCore();
        _toposCoreAddr = toposCoreAddr;
    }

    /// @notice Entry point for executing any message on a target subnet
    /// @param indexOfDataInTxRaw Index of tx.data in raw transaction hex
    /// @param txRaw RLP encoded raw transaction hex
    /// @param proofBlob RLP encoded proof blob
    /// @param txRoot Transactions root
    function execute(
        uint256 indexOfDataInTxRaw,
        bytes calldata proofBlob,
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

        if (_isTxExecuted(txHash)) revert TransactionAlreadyExecuted();

        // prevent re-entrancy
        _setTxExecuted(txHash);
        _execute(indexOfDataInTxRaw, txRaw);
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

    /// @notice Execute the message on a target subnet
    /// @dev This function should be implemented by the child contract
    /// @param indexOfDataInTxRaw Index of tx.data in raw transaction hex
    /// @param txRaw RLP encoded raw transaction hex
    function _execute(uint256 indexOfDataInTxRaw, bytes calldata txRaw) internal virtual {}

    /// @notice emit a message sent event from the ToposCore contract
    function _emitMessageSentEvent(SubnetId targetSubnetId, bytes memory data) internal {
        IToposCore(_toposCoreAddr).emitCrossSubnetMessage(targetSubnetId, data);
    }

    /// @notice Set a flag to indicate that the asset transfer transaction has been executed
    /// @param txHash Hash of asset transfer transaction
    function _setTxExecuted(bytes32 txHash) internal {
        _setBool(_getTxExecutedKey(txHash), true);
    }

    /// @notice Get the flag to indicate that the transaction has been executed
    /// @param txHash transaction hash
    function _isTxExecuted(bytes32 txHash) internal view returns (bool) {
        return getBool(_getTxExecutedKey(txHash));
    }

    /// @notice Validate that the target subnet id is the same as the subnet id of the topos core
    /// @param targetSubnetId Subnet id of the target subnet
    function _validateTargetSubnetId(SubnetId targetSubnetId) internal view returns (bool) {
        SubnetId toposCoreSubnetId = IToposCore(_toposCoreAddr).networkSubnetId();
        return (SubnetId.unwrap(targetSubnetId) == SubnetId.unwrap(toposCoreSubnetId));
    }

    /// @notice Get the key for the flag to indicate that the transaction has been executed
    /// @param txHash transaction hash
    function _getTxExecutedKey(bytes32 txHash) internal pure returns (bytes32) {
        return keccak256(abi.encode(PREFIX_EXECUTED, txHash));
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
    /// @param skipNibbles number of nibbles to skip
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
