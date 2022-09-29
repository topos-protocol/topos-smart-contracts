// SPDX-License-Identifier: MIT
pragma solidity ^0.8.9;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "../../interfaces/topos-core-contracts/IToposCoreContract.sol";
import "../../interfaces/misc/IToposERC20Base.sol";
import "./CrossSubnetInterface.sol";

contract ToposCoreContract is AccessControl, IToposCoreContract {
    /// @notice Validator role
    /// 0xa95257aebefccffaada4758f028bce81ea992693be70592f620c4c9a0d9e715a
    bytes32 public constant VALIDATOR = keccak256(abi.encodePacked("VALIDATOR"));

    /// @notice The subnet ID of the subnet this contract is deployed on
    /// @dev Must be set in the constructor
    uint64 public subnetId;

    /// @notice Mapping to store validated certificates
    /// @dev certId => certificate
    mapping(bytes => CrossSubnetInterface.Certificate) _validatedCerts;

    /// @notice Check for the validator role
    modifier onlyValidator() {
        require(hasRole(VALIDATOR, msg.sender), "onlyValidator: bad role");
        _;
    }

    /// @notice Constructor
    /// @param _subnetId subnet ID of the subnet this contract is deployed on
    /// @param _validator validator's address
    constructor(uint64 _subnetId, address _validator) {
        subnetId = _subnetId;
        _grantRole(VALIDATOR, _validator);
    }

    /// @notice Verify an incoming certificate from the topos-node
    /// @param cert incoming certificate
    /// Todo: Not sure what type of input we want so, parse and implement accordingly
    function verifyCertificate(CrossSubnetInterface.Certificate calldata cert) public onlyValidator {
        CrossSubnetInterface.Certificate memory storedCert = validatedCerts(cert.certId);
        require(storedCert.isPresent == false, "Certificate already verified");
        require(_validateCertificate(cert), "Invalid certificate");
        _validatedCerts[cert.certId] = cert;
    }

    /// @notice Execute a single cross-subnet message
    /// @dev Can be called by anybody
    /// @param certId certificate id
    /// @param xsMsgId message id (to be determined)
    function executeXsMessage(bytes calldata certId, bytes calldata xsMsgId) public {
        CrossSubnetInterface.Certificate memory storedCert = validatedCerts(certId);
        require(storedCert.isPresent, "Certificate not found");
        CrossSubnetInterface.CrossSubnetMessage memory xsMessage = getXsMessage(xsMsgId, storedCert);
        require(xsMessage.xsMsgId.length != 0, "Cross-subnet message not found");

        bytes32 xsMessageHash = keccak256(abi.encodePacked(certId, xsMsgId));
        if (xsMessage.transactionType == CrossSubnetInterface.TransactionType.AssetTransfer) {
            IToposERC20Base(xsMessage.xsAssetTransfer.toTokenAddr).mintFromXsMsg(certId, xsMsgId);
            IToposERC20Base(xsMessage.xsFee.feeTokenAddr).transferXsMsgFee(certId, xsMsgId, msg.sender);
            IToposERC20Base(xsMessage.xsAssetTransfer.toTokenAddr).addProcessedXsMessage(xsMessageHash);
        }
    }

    /// @notice Gets the validated certificates
    /// @dev Getter function to the private _validatedCerts
    /// @param certId certificate id
    /// @return Certificate returns the certificate for the certificate id
    function validatedCerts(bytes calldata certId)
        public
        view
        override
        returns (CrossSubnetInterface.Certificate memory)
    {
        return _validatedCerts[certId];
    }

    /// @notice Get a cross-subnet message from cross-subnet messages list
    /// @param xsMsgId cross-subnet message ID
    /// @param cert certificate
    /// @return CrossSubnetMessage a list of all cross-subnet messages
    function getXsMessage(bytes calldata xsMsgId, CrossSubnetInterface.Certificate memory cert)
        public
        pure
        returns (CrossSubnetInterface.CrossSubnetMessage memory)
    {
        CrossSubnetInterface.CrossSubnetMessage memory xsMessage;
        for (uint256 i = 0; i < cert.xsMessages.length; i++) {
            if (keccak256(abi.encodePacked(cert.xsMessages[i].xsMsgId)) == keccak256(abi.encodePacked(xsMsgId))) {
                xsMessage = cert.xsMessages[i];
                break;
            }
        }
        return xsMessage;
    }

    /// @notice Validates the certificate
    /// @param @param cert incoming certificate
    function _validateCertificate(
        CrossSubnetInterface.Certificate calldata /*cert*/
    ) internal pure returns (bool) {
        return true;
    }

    /// @notice Convenient function to convert bytes to uint256
    /// @param @param b bytes to convert
    function _bytesToUint(bytes memory b) internal pure returns (uint256) {
        uint256 number;
        for (uint256 i = 0; i < b.length; i++) {
            number = number + uint256(uint8(b[i])) * (2**(8 * (b.length - (i + 1))));
        }
        return number;
    }
}
