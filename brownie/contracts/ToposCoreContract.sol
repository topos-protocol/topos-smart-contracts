// SPDX-License-Identifier: MIT
pragma solidity ^0.8.9;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/proxy/Clones.sol";
import "./Asset.sol";
import "../interfaces/IAsset.sol";

contract ToposCoreContract is Ownable {
    struct CrossSubnetMessage {
        uint256 sendingSubnetId;
        CrossChainTransaction[] inputs;
        uint256 isTypeOf;
    }

    struct CrossChainTransaction {
        uint256 recipientSubnetId;
        string assetId;
        address recipientAddr;
        uint256 amount;
    }

    struct AssetContainer {
        string assetId;
        address contractAddr;
        string symbol;
        bool isPresent;
    }

    // Types of cross-subnet messages
    enum IsTypeOf {
        Inbound,
        Outbound
    }

    // Address of the Asset clone implementation
    address immutable _assetImplementation;

    // Subnet Id this contract was deployed for
    uint256 public subnetId;

    // List of all the known assets on a subnet
    mapping(string => AssetContainer) public knownAssets;

    // Mapping to store claimableBalances for all assets for a receiver
    mapping(address => mapping(address => uint256)) public claimableBalances;

    // Event to store cross-subnet message data on the blockchain
    event Sent(uint256 terminalSubnetId, string assetId, address recipientAddr, uint256 amount);

    // Event to know if the certificate was applied successfully
    event CertificateApplied(bool success);

    // Constructor
    constructor(uint256 _subnetId) {
        subnetId = _subnetId;
        _assetImplementation = address(new Asset());
    }

    // Send an amount to another Subnet
    function sendToken(
        address _sourceAssetAddr,
        uint256 _recipientSubnetId,
        string memory _assetId,
        address _recipientAddr,
        uint256 _amount
    ) public payable {
        require(_amount > 0, "Amount cannot be zero");
        // Lock the amount to be sent to the receiving Subnet in
        // Topos Core contract address (making it unspendable)
        // Todo: come up with a proper burning mechanism
        IAsset(_sourceAssetAddr).transferFrom(msg.sender, address(this), _amount);

        // Events are stored on the runtime storage
        // and can be accessed at any point in time,
        // except if there are re-orgs on the blockchain.
        // This should not be a problem if the blockchain
        // employes a finality gadget like Grandpa.
        emit Sent(_recipientSubnetId, _assetId, _recipientAddr, _amount);
    }

    // Mint the amount on the receivers end
    function mint(
        bytes memory, /*_cert*/
        CrossSubnetMessage memory _crossSubnetMessage
    ) public onlyOwner {
        require(_crossSubnetMessage.sendingSubnetId == subnetId, "Subnet ID is invalid");
        require(_crossSubnetMessage.isTypeOf == uint256(IsTypeOf.Inbound), "Type of cross-subnet message is invalid");
        // Todo: require(_validateCert(_cert) == true, "Certificate is invalid");

        for (uint256 i = 0; i < _crossSubnetMessage.inputs.length; i++) {
            if (knownAssets[_crossSubnetMessage.inputs[i].assetId].isPresent == false) {
                address recipientAddr = _crossSubnetMessage.inputs[i].recipientAddr;
                address recipientContractAddr = deployContract(
                    "TEST",
                    "TST",
                    2**256 - 1,
                    _crossSubnetMessage.inputs[i].assetId
                );
                claimableBalances[recipientContractAddr][recipientAddr] += _crossSubnetMessage.inputs[i].amount;
            } else {
                address recipientContractAddr = _getAssetAddress(_crossSubnetMessage.inputs[i].assetId);
                claimableBalances[recipientContractAddr][recipientAddr] += _crossSubnetMessage.inputs[i].amount;
            }
        }
        emit CertificateApplied(true);
    }

    // Function to claim the amount that is accumulated in the claimableBalances mapping
    // after a certificate is processed
    function claimTransfer(address _assetContractAddr) public payable {
        uint256 amount = claimableBalances[_assetContractAddr][msg.sender];
        require(amount > 0, "No amount to claim");
        claimableBalances[_assetContractAddr][msg.sender] -= amount;
        IAsset(_assetContractAddr).mint(msg.sender, amount);
    }

    // Function to create a proxy contract for the Asset
    function deployContract(
        string memory _name,
        string memory _symbol,
        uint256 _initialSupply,
        string memory _assetId
    ) private returns (address) {
        address assetCloneAddr = Clones.clone(_assetImplementation);
        Asset(assetCloneAddr).initialize(_name, _symbol, _initialSupply);
        AssetContainer memory asset = AssetContainer(_assetId, assetCloneAddr, _symbol, true);
        knownAssets[_assetId] = asset;
        return assetCloneAddr;
    }

    // Function to be used internally to fetch the asset's contract address (if any)
    // if the assetId is provided
    function _getAssetAddress(string memory _assetId) private view returns (address) {
        AssetContainer memory asset = knownAssets[_assetId];
        return asset.contractAddr;
    }
}
