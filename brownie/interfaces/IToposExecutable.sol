// SPDX-License-Identifier: MIT

pragma solidity ^0.8.9;

import {IToposCoreContract, subnetId} from "./IToposCoreContract.sol";

interface IToposExecutable {
    error InvalidAddress();
    error InvalidCallData();
    error NotApprovedByToposCoreContract();

    function toposCoreContract() external view returns (IToposCoreContract);

    function execute(
        bytes calldata certId,
        bytes32 commandId,
        subnetId destinationSubnetId,
        address destinationContractAddress,
        bytes calldata payload
    ) external;

    function executeWithToken(
        bytes calldata certId,
        bytes32 commandId,
        subnetId destinationSubnetId,
        address destinationContractAddress,
        bytes calldata payload,
        string calldata tokenSymbol,
        uint256 amount
    ) external;
}
