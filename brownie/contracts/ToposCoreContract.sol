// SPDX-License-Identifier: MIT
pragma solidity ^0.8.9;

import "../interfaces/IAsset.sol";

/// @title ToposCoreContract
/// @notice This contract can be used to initiate and receive cross-subnet transactions
/// @dev To be deployed on sending and receiving subnets prior to registration on the Topos subnet
contract ToposCoreContract {
    struct CrossSubnetMessage {
        uint64 subnetId; // subnet ID of the initial subnet
        CrossChainTransaction[] inputs; // cross-subnet transaction data
        uint256 isTypeOf; // type of cross-subnet message inbound/outbound
    }

    struct CrossChainTransaction {
        uint64 terminalSubnetId; // subnet ID of the terminal subnet
        address terminalContractAddr; // contract address of the recipient token
        address recipientAddr; // address of the recipient
        uint256 amount; // amount to transfer
    }

    /// @notice Types of cross-subnet messages
    enum IsTypeOf {
        Inbound,
        Outbound
    }

    /// @notice Subnet ID this contract was deployed for
    uint64 public subnetId;

    /// @notice Mapping to store balances to be claimed by the recipient once they are minted
    mapping(address => mapping(address => uint256)) public claimableBalances;

    /// @notice Event to be stored on the blockchain with the data
    event Sent(uint64 terminalSubnetId, address terminalContractAddr, address recipientAddr, uint256 amount);

    /// @notice Event to know if the certificate was applied successfully
    event CertificateApplied(bool success);

    /// Constructor
    constructor(uint64 _subnetId) {
        subnetId = _subnetId;
    }

    /// @notice Initiate a cross-chain transaction
    /// @dev ERC20 token needs to grant some allowance for the ToposSmartContract
    /// @param _sourceTokenAddr Contract address from where the funds are to be sent
    /// @param _terminalSubnetId Subnet ID of the terminal subnet
    /// @param _terminalContractAddr Contract address of the recipient token
    /// @param _recipientAddr Address of the recipient
    /// @param _amount Amount to transfer
    function sendToken(
        address _sourceTokenAddr,
        uint64 _terminalSubnetId,
        address _terminalContractAddr,
        address _recipientAddr,
        uint256 _amount
    ) public payable {
        require(_amount > 0, "Amount cannot be zero");
        // Lock the amount to be sent to the receiving subnet in
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

    /// @notice Mint the amount for a recipient token/user
    /// @dev This function is to be used by the stakeholders of the recipient subnet
    /// @param // _cert Incoming certificate
    /// @param _crossSubnetMessage Cross-subnet message containing the cross-chain transaction
    function mint(bytes memory, CrossSubnetMessage memory _crossSubnetMessage) public {
        require(_crossSubnetMessage.subnetId == subnetId, "Subnet ID is invalid");
        require(_crossSubnetMessage.isTypeOf == uint256(IsTypeOf.Inbound), "Type of cross-subnet message is invalid");
        // TODO: require(_validateCert(_cert) == true, "Certificate is invalid");

        for (uint256 i = 0; i < _crossSubnetMessage.inputs.length; i++) {
            address terminalContractAddr = _crossSubnetMessage.inputs[i].terminalContractAddr;
            address recipientAddr = _crossSubnetMessage.inputs[i].recipientAddr;
            claimableBalances[terminalContractAddr][recipientAddr] += _crossSubnetMessage.inputs[i].amount;
        }
        emit CertificateApplied(true);
    }

    /// @notice Claim the minted funds for the recipient token/user
    /// @dev [msg.sender] allows only the rightful owner of the minted amount to claim funds
    /// @param token Contract address for the recipient token
    function claimTransfer(address token) public payable {
        uint256 amount = claimableBalances[token][msg.sender];
        require(amount > 0, "No amount to claim");
        claimableBalances[token][msg.sender] -= amount;
        IAsset(token).mint(msg.sender, amount);
    }
}
