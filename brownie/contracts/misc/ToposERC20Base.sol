// SPDX-License-Identifier: MIT
pragma solidity ^0.8.2;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "../../interfaces/misc/IToposERC20Base.sol";

/// @title ToposERC20Base
/// @notice This contract can be used as any ERC20 token base contract to initiate and receive cross-subnet transactions
contract ToposERC20Base is ERC20, IToposERC20Base {
    /// @notice The Topos Core contract address
    /// @dev Must be specified in the constructor
    address public immutable toposCoreContractAddr;

    /// @notice Event emitted on successfully sending a cross-subnet asset transfer transaction
    /// @param xsAssetTransfer cross-subnet asset transfer transaction info
    /// @param xsFee cross-subnet message fee
    event AssetTransferTxSent(CrossSubnetAssetTransfer xsAssetTransfer, CrossSubnetFee xsFee);

    /// @notice Event emitted on successfully sending a cross-subnet remote call transaction
    /// @param xsRemoteCall cross-subnet remote call transaction info
    /// @param xsFee cross-subnet message fee
    event RemoteCallTxSent(CrossSubnetRemoteCall xsRemoteCall, CrossSubnetFee xsFee);

    /// @notice Modifier to restrict access to only from the Topos Core Contract
    modifier onlyToposCoreContract() {
        require(msg.sender == toposCoreContractAddr, "Only callable by the Topos Core contract");
        _;
    }

    /// @notice Mints an initial supply for the deployer
    /// @param name name of token
    /// @param symbol symbol for token
    /// @param initialSupply initial total supply
    /// @param _toposCoreContractAddr Topos Core contract address
    constructor(
        string memory name,
        string memory symbol,
        uint256 initialSupply,
        address _toposCoreContractAddr
    ) ERC20(name, symbol) {
        _mint(msg.sender, initialSupply);
        toposCoreContractAddr = _toposCoreContractAddr;
    }

    /// @notice Send a cross-subnet message to another subnet
    /// @dev Users need to make sure the input they provide is correct
    /// @param xsMsg cross-subnet message information
    function sendToSubnet(CrossSubnetMessage memory xsMsg) public {
        if (xsMsg.transferType == TransactionType.AssetTransfer) {
            _burn(msg.sender, xsMsg.xsAssetTransfer.amount);
            emit AssetTransferTxSent(xsMsg.xsAssetTransfer, xsMsg.xsFee);
        }
    }

    /// @notice Explain to an end user what this does
    /// @dev Explain to a developer any extra details
    /// @param certId certificate ID of the certificate to get the message from
    /// @param xsMsgId cross-subnet message ID
    function mintFromxsMsg(bytes calldata certId, bytes calldata xsMsgId) public onlyToposCoreContract {}
}
