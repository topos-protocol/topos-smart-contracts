// SPDX-License-Identifier: MIT

pragma solidity ^0.8.9;

import {IToposCore, CertificateId, SubnetId} from "./IToposCore.sol";

interface IToposExecutable {
    struct ContractCallData {
        bytes txHash;
        SubnetId sourceSubnetId;
        address sourceContractAddr;
        SubnetId targetSubnetId;
        address targetContractAddr;
        bytes payload;
        bytes32 selector; // keccak256 hash of a function name eg. keccak256("executeContractCall")
    }

    struct ContractCallWithTokenData {
        bytes txHash;
        SubnetId sourceSubnetId;
        address sourceContractAddr;
        SubnetId targetSubnetId;
        address targetContractAddr;
        bytes payload;
        string symbol;
        uint256 amount;
        bytes32 selector;
    }

    event OriginAuthorized(SubnetId sourceSubnetId, address sourceContractAddr, bytes32 selector);

    error NotAdmin();
    error InvalidAddress();
    error InvalidCallData();
    error ContractCallAlreadyExecuted();
    error UnauthorizedOrigin();

    function authorizeOrigin(SubnetId sourceSubnetId, address sourceContractAddr, bytes32 selector) external;

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

    function toposCore() external view returns (IToposCore);
}
