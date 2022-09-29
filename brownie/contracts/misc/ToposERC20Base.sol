// SPDX-License-Identifier: MIT
pragma solidity ^0.8.2;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "../../interfaces/topos-core-contracts/IToposCoreContract.sol";
import "../../interfaces/misc/IToposERC20Base.sol";
import "../topos-core-contracts/CrossSubnetInterface.sol";

/// @title ToposERC20Base
/// @notice This contract can be used as any ERC20 token base contract to initiate and receive cross-subnet transactions
contract ToposERC20Base is ERC20, IToposERC20Base {
    /// @notice The Topos Core contract address
    /// @dev Must be specified in the constructor
    address public immutable toposCoreContractAddr;

    /// @notice The subnet ID of the subnet this contract is deployed on
    /// @dev Must be set in the constructor
    uint64 public immutable subnetId;

    /// @notice A mapping to store all the processed cross-subnet messages
    /// @dev (keccak256(certId,xsMsgId) => isProcessed)
    mapping(bytes32 => bool) public processedXsMessages;

    /// @notice Event emitted on successfully sending a cross-subnet asset transfer transaction
    /// @param xsAssetTransfer cross-subnet asset transfer transaction info
    /// @param xsFee cross-subnet message fee
    event AssetTransferTxSent(
        bytes xsMsgId,
        CrossSubnetInterface.CrossSubnetAssetTransfer xsAssetTransfer,
        CrossSubnetInterface.CrossSubnetFee xsFee,
        uint256 xsTransactionType
    );

    /// @notice Event emitted on successfully sending a cross-subnet remote call transaction
    /// @param xsRemoteCall cross-subnet remote call transaction info
    /// @param xsFee cross-subnet message fee
    event RemoteCallTxSent(
        CrossSubnetInterface.CrossSubnetRemoteCall xsRemoteCall,
        CrossSubnetInterface.CrossSubnetFee xsFee
    );

    /// @notice Modifier to restrict access to only from the Topos Core Contract
    modifier onlyToposCoreContract() {
        require(msg.sender == toposCoreContractAddr, "Only callable by the Topos Core contract.");
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
        address _toposCoreContractAddr,
        uint64 _subnetId
    ) ERC20(name, symbol) {
        _mint(msg.sender, initialSupply);
        toposCoreContractAddr = _toposCoreContractAddr;
        subnetId = _subnetId;
    }

    /// @notice Send a cross-subnet message to another subnet
    /// @dev Users need to make sure the input they provide is correct
    /// @param xsMsg cross-subnet message information
    function sendToSubnet(CrossSubnetInterface.CrossSubnetMessage memory xsMsg) public {
        require(
            xsMsg.transactionType == CrossSubnetInterface.TransactionType.AssetTransfer,
            "Transaction type not correct"
        );
        _burn(msg.sender, xsMsg.xsAssetTransfer.amount);
        emit AssetTransferTxSent(xsMsg.xsMsgId, xsMsg.xsAssetTransfer, xsMsg.xsFee, uint256(xsMsg.transactionType));
    }

    /// @notice Explain to an end user what this does
    /// @dev Explain to a developer any extra details
    /// @param certId certificate ID of the certificate to get the message from
    /// @param xsMsgId cross-subnet message ID
    function mintFromXsMsg(bytes calldata certId, bytes calldata xsMsgId) public onlyToposCoreContract {
        CrossSubnetInterface.Certificate memory storedCert = IToposCoreContract(toposCoreContractAddr).validatedCerts(
            certId
        );
        require(storedCert.certId.length != 0, "Certificate not found");

        CrossSubnetInterface.CrossSubnetMessage memory xsMsg = IToposCoreContract(toposCoreContractAddr).getXsMessage(
            xsMsgId,
            storedCert
        );
        require(xsMsg.xsMsgId.length != 0, "Cross-subnet message not found");
        require(xsMsg.toSubnetId == subnetId, "Incorrect subnet ID");
        require(xsMsg.xsAssetTransfer.toTokenAddr == address(this), "Incorrect Token address");

        bytes32 xsMessageHash = keccak256(abi.encodePacked(certId, xsMsgId));
        require(processedXsMessages[xsMessageHash] == false, "Cross subnet message already processed");
        if (xsMsg.transactionType == CrossSubnetInterface.TransactionType.AssetTransfer) {
            _mint(xsMsg.xsAssetTransfer.to, xsMsg.xsAssetTransfer.amount);
        }
    }

    /// @notice Explain to an end user what this does
    /// @dev Explain to a developer any extra details
    /// @param certId certificate ID of the certificate to get the message from
    /// @param xsMsgId cross-subnet message ID
    /// @param receiver address of the fee receiver
    function transferXsMsgFee(
        bytes calldata certId,
        bytes calldata xsMsgId,
        address receiver
    ) public onlyToposCoreContract {
        CrossSubnetInterface.Certificate memory storedCert = IToposCoreContract(toposCoreContractAddr).validatedCerts(
            certId
        );
        require(storedCert.certId.length != 0, "Certificate not found");

        CrossSubnetInterface.CrossSubnetMessage memory xsMsg = IToposCoreContract(toposCoreContractAddr).getXsMessage(
            xsMsgId,
            storedCert
        );
        require(xsMsg.xsMsgId.length != 0, "Cross-subnet message not found");
        require(xsMsg.toSubnetId == subnetId, "Incorrect subnet ID");
        require(xsMsg.xsFee.feeTokenAddr == address(this), "Incorrect fee Token address");

        bytes32 xsMessageHash = keccak256(abi.encodePacked(certId, xsMsgId));
        require(processedXsMessages[xsMessageHash] == false, "Cross subnet message already processed");
        _mint(receiver, xsMsg.xsFee.feeAmount);
    }

    /// @notice Add cross-subnet message to processed storage
    /// @dev only accessible by Topos Core Contract
    /// @param xSMsgHash keccak256(certId,xsMsgId)
    function addProcessedXsMessage(bytes32 xSMsgHash) public onlyToposCoreContract {
        require(processedXsMessages[xSMsgHash] == false, "Cross subnet message already processed");
        processedXsMessages[xSMsgHash] = true;
    }
}
