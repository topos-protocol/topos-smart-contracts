// SPDX-License-Identifier: MIT

pragma solidity ^0.8.9;

import {IToposCoreContract, subnetId} from "./IToposCoreContract.sol";

interface IToposExecutable {
    error NotAdmin();
    error InvalidAddress();
    error InvalidCallData();
    error ContractCallAlreadyExecuted();
    error UnauthorizedOrigin();

    event OriginAuthorized(subnetId originSubnetId, address originAddress, bytes32 selector, uint256 minimumCertHeight);

    struct ContractCallData {
        bytes txHash;
        subnetId originSubnetId;
        address originAddress;
        subnetId destinationSubnetId;
        address destinationContractAddress;
        bytes32 payloadHash;
        bytes payload;
        bytes32 selector; // keccak256 hash of a function name eg. keccak256("executeContractCall")
    }

    struct ContractCallWithTokenData {
        bytes txHash;
        subnetId originSubnetId;
        address originAddress;
        subnetId destinationSubnetId;
        address destinationContractAddress;
        bytes32 payloadHash;
        bytes payload;
        string symbol;
        uint256 amount;
        bytes32 selector;
    }

    function toposCoreContract() external view returns (IToposCoreContract);

    function authorizeOrigin(
        subnetId originSubnetId,
        address originAddress,
        bytes32 selector,
        uint256 minimumCertHeight
    ) external;

    function execute(
        bytes calldata certId,
        ContractCallData memory contractCallData,
        bytes calldata crossSubnetTxProof
    ) external;

    function executeWithToken(
        bytes calldata certId,
        ContractCallWithTokenData memory contractCallWithTokenData,
        bytes calldata crossSubnetTxProof
    ) external;
}
