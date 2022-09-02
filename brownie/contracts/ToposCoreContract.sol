// SPDX-License-Identifier: MIT
pragma solidity ^0.8.9;

import "../interfaces/IAsset.sol";

contract ToposCoreContract {
    struct CrossSubnetMessage {
        uint64 subnetId;
        CrossChainTransaction[] inputs;
        uint256 isTypeOf;
    }

    struct CrossChainTransaction {
        uint64 terminalSubnetId;
        address terminalContractAddr;
        address recipientAddr;
        uint256 amount;
    }

    // Types of cross-subnet messages
    enum IsTypeOf {
        Inbound,
        Outbound
    }

    // Subnet Id this contract was deployed for
    uint64 public subnetId;

    // Mapping to store balances for all tokens
    mapping(address => mapping(address => uint256)) public balances;

    // Event to be stored on the blockchain with the data
    event Sent(uint64 terminalSubnetId, address terminalContractAddr, address recipientAddr, uint256 amount);

    // Event to get the response of the low level call
    event Response(bool success, bytes data);

    // Event to know if the certificate was applied successfully
    event CertificateApplied(bool success);

    // Constructor
    constructor(uint64 _subnetId) {
        subnetId = _subnetId;
    }

    // Send an amount to another Subnet
    function sendToken(
        address _sourceTokenAddr,
        uint64 _terminalSubnetId,
        address _terminalContractAddr,
        address _recipientAddr,
        uint256 _amount
    ) public payable {
        require(_amount > 0, "Amount cannot be zero");
        // Lock the amount to be sent to the receiving Subnet in
        // Topos Core contract address (making it unspendable)
        // Todo: come up with a proper burning mechanism
        IAsset(_sourceTokenAddr).transferFrom(msg.sender, address(this), _amount);

        // Events are stored on the runtime storage
        // and can be accessed at any point in time,
        // except if there are re-orgs on the blockchain.
        // This should not be a problem if the blockchain
        // employes a finality gadget like Grandpa.
        emit Sent(_terminalSubnetId, _terminalContractAddr, _recipientAddr, _amount);
    }

    // Mint the amount on the receivers end
    function mint(
        bytes memory, /*_cert*/
        CrossSubnetMessage memory _crossSubnetMessage
    ) public {
        require(_crossSubnetMessage.subnetId == subnetId, "Subnet ID is invalid");
        require(_crossSubnetMessage.isTypeOf == uint256(IsTypeOf.Inbound), "Type of cross-subnet message is invalid");
        // Todo: require(_validateCert(_cert) == true, "Certificate is invalid");

        for (uint256 i = 0; i < _crossSubnetMessage.inputs.length; i++) {
            address terminalContractAddr = _crossSubnetMessage.inputs[i].terminalContractAddr;
            address recipientAddr = _crossSubnetMessage.inputs[i].recipientAddr;
            balances[terminalContractAddr][recipientAddr] += _crossSubnetMessage.inputs[i].amount;
        }
        emit CertificateApplied(true);
    }

    // Function to claim the amount that is accumulated in the balances mapping
    // after a certificate is processed
    function claimTransfer(address token) public payable {
        uint256 amount = balances[token][msg.sender];
        require(amount > 0, "No amount to claim");
        balances[token][msg.sender] -= amount;
        IAsset(token).mint(msg.sender, amount);
    }
}
