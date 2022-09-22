// SPDX-License-Identifier: MIT
pragma solidity ^0.8.2;

import "../../interfaces/misc/IToposERC20Base.sol";

interface IToposCoreContract is IToposERC20Base {
    /// @notice A container for store certificates
    struct Certificate {
        uint64 initialSubnetId;
        bytes certId;
        bytes previousCertId;
        bool isPresent;
        CrossSubnetMessage[] xsMessages;
    }

    function verifyCertificate(bytes[] calldata cert) external;

    function executeXsMessage(bytes calldata certId, bytes calldata xsMessageId) external;
}
