// SPDX-License-Identifier: MIT
pragma solidity ^0.8.9;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "../../interfaces/topos-core-contract/IToposCoreContract.sol";
import "../../interfaces/misc/IToposERC20Base.sol";

abstract contract ToposCoreContract is AccessControl, IToposCoreContract {
    /// @notice Validator role
    /// 0xa95257aebefccffaada4758f028bce81ea992693be70592f620c4c9a0d9e715a
    bytes32 public constant VALIDATOR = keccak256(abi.encodePacked("VALIDATOR"));

    /// @notice The subnet ID of the subnet this contract is deployed on
    /// @dev Must be set in the constructor
    uint64 public subnetId;

    /// @notice Mapping to store validated certificates
    /// @dev certId => certificate
    mapping(bytes => Certificate) public validatedCerts;

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
    function verifyCertificate(Certificate calldata cert) public onlyValidator {
        Certificate storage storedCert = validatedCerts[cert.certId];
        require(storedCert.isPresent, "Certificate already verified");
        require(_validateCertificate(cert), "Invalid certificate");
        validatedCerts[cert.certId] = cert;
    }

    /// @notice Execute a single cross-subnet message
    /// @dev Can be called by anybody
    /// @param certId certificate id
    /// @param xsMessageId message id (to be determined)
    function executeXsMessage(bytes calldata certId, bytes calldata xsMessageId) public {
        Certificate storage storedCert = validatedCerts[certId];
        require(storedCert.isPresent, "Certificate not found");
        require(_getXsMessageCount(xsMessageId, storedCert.xsMessages) != 0, "Cross-subnet message not found");

        // IToposERC20Base.mintFromxsMsg(certId, xsMessageId); // Todo: To be implemented
    }

    /// @notice Get a cross-subnet message from cross-subnet messages list
    /// @param @param xsMessageId cross-subnet message ID
    /// @param @param _xsMessagesList cross-subnet message list
    function _getXsMessageCount(bytes calldata xsMessageId, CrossSubnetMessage[] storage _xsMessagesList)
        internal
        view
        returns (uint256)
    {
        uint256 count = 0;
        for (uint256 i = 0; i < _xsMessagesList.length; i++) {
            if (keccak256(abi.encodePacked(_xsMessagesList[i].xsMsgId)) == keccak256(abi.encodePacked(xsMessageId))) {
                count + 1;
            }
        }
        return count;
    }

    /// @notice Validates the certificate
    /// @param @param cert incoming certificate
    function _validateCertificate(Certificate calldata cert) internal pure returns (bool) {
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
