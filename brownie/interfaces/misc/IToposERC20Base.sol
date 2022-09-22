// SPDX-License-Identifier: MIT
pragma solidity ^0.8.2;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

interface IToposERC20Base is IERC20 {
    /// @notice A container for the cross-subnet asset transfer transaction
    struct CrossSubnetAssetTransfer {
        uint64 toSubnetId;
        address toTokenAddr;
        address to;
        address from;
        uint256 amount;
    }

    /// @notice A container for the cross-subnet remote call transaction
    struct CrossSubnetRemoteCall {
        uint64 toSubnetId;
        address toTokenAddr;
        bytes call;
        bytes[] arguments;
    }

    /// @notice A container for the fee payment information
    struct CrossSubnetFee {
        address feePayerAddr;
        address feeTokenAddr;
        uint256 feeAmount;
    }

    /// @notice A unified container to put the collective cross-subnet transaction info
    struct CrossSubnetMessage {
        bytes xsMsgId;
        CrossSubnetAssetTransfer xsAssetTransfer;
        CrossSubnetRemoteCall xsRemoteCall;
        CrossSubnetFee xsFee;
        TransactionType transferType;
    }

    /// @notice Type of cross-subnet transactions
    enum TransactionType {
        AssetTransfer,
        RemoteContractCall
    }

    function sendToSubnet(CrossSubnetMessage memory xsMsg) external;

    function mintFromxsMsg(bytes calldata certId, bytes calldata xsMsgId) external;
}
