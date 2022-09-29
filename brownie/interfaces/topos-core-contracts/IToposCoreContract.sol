// SPDX-License-Identifier: MIT
pragma solidity ^0.8.2;

import "../../contracts/topos-core-contracts/CrossSubnetInterface.sol";

interface IToposCoreContract {
    function verifyCertificate(CrossSubnetInterface.Certificate calldata cert) external;

    function executeXsMessage(bytes calldata certId, bytes calldata xsMsgId) external;

    function validatedCerts(bytes calldata certId) external returns (CrossSubnetInterface.Certificate memory);

    function getXsMessage(bytes calldata xsMsgId, CrossSubnetInterface.Certificate memory cert)
        external
        returns (CrossSubnetInterface.CrossSubnetMessage memory);
}
