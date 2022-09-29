// SPDX-License-Identifier: MIT
pragma solidity ^0.8.2;

library CrossSubnetInterface {
    /// @notice A container for the cross-subnet asset transfer transaction
    struct CrossSubnetAssetTransfer {
        address toTokenAddr;
        address to;
        address from;
        uint256 amount;
    }

    /// @notice A container for the cross-subnet remote call transaction
    struct CrossSubnetRemoteCall {
        address toTokenAddr;
        bytes call;
        bytes[] arguments;
    }

    /// @notice A container for the fee payment information
    struct CrossSubnetFee {
        address feeTokenAddr;
        uint256 feeAmount;
    }

    /// @notice A unified container to put the collective cross-subnet transaction info
    struct CrossSubnetMessage {
        bytes xsMsgId;
        uint64 toSubnetId;
        CrossSubnetAssetTransfer xsAssetTransfer;
        CrossSubnetRemoteCall xsRemoteCall;
        CrossSubnetFee xsFee;
        TransactionType transactionType;
    }

    /// @notice Type of cross-subnet transactions
    enum TransactionType {
        AssetTransfer,
        RemoteContractCall
    }

    /// @notice A container for store certificates
    struct Certificate {
        uint64 initialSubnetId;
        bytes certId;
        bytes previousCertId;
        bool isPresent;
        CrossSubnetMessage[] xsMessages;
    }
}
