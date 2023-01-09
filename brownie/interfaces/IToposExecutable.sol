// SPDX-License-Identifier: MIT

pragma solidity ^0.8.9;

import {IToposCoreContract, CertificateId, subnetId} from "./IToposCoreContract.sol";

interface IToposExecutable {
    error NotAdmin();
    error InvalidAddress();
    error InvalidCallData();
    error ContractCallAlreadyExecuted();
    error UnauthorizedOrigin();

    event OriginAuthorized(
        subnetId sourceSubnetId,
        address sourceContractAddr,
        bytes32 selector,
        uint256 minimumCertPosition
    );

    struct ContractCallData {
        bytes txHash;
        subnetId sourceSubnetId;
        address sourceContractAddr;
        subnetId targetSubnetId;
        address targetContractAddr;
        bytes32 payloadHash;
        bytes payload;
        bytes32 selector; // keccak256 hash of a function name eg. keccak256("executeContractCall")
    }

    struct ContractCallWithTokenData {
        bytes txHash;
        subnetId sourceSubnetId;
        address sourceContractAddr;
        subnetId targetSubnetId;
        address targetContractAddr;
        bytes32 payloadHash;
        bytes payload;
        string symbol;
        uint256 amount;
        bytes32 selector;
    }

    function toposCoreContract() external view returns (IToposCoreContract);

    function authorizeOrigin(
        subnetId sourceSubnetId,
        address sourceContractAddr,
        bytes32 selector,
        uint256 minimumCertPosition
    ) external;

    function execute(
        CertificateId certId,
        ContractCallData memory contractCallData,
        bytes calldata crossSubnetTxProof
    ) external;

    function executeWithToken(
        CertificateId certId,
        ContractCallWithTokenData memory contractCallWithTokenData,
        bytes calldata crossSubnetTxProof
    ) external;
}
