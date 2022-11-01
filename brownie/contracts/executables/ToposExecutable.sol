// SPDX-License-Identifier: MIT

pragma solidity ^0.8.9;

import {IToposCoreContract, subnetId} from "./../../interfaces/IToposCoreContract.sol";
import {IToposExecutable} from "./../../interfaces/IToposExecutable.sol";

contract ToposExecutable is IToposExecutable {
    IToposCoreContract public immutable toposCoreContract;

    constructor(address toposCoreContract_) {
        if (toposCoreContract_ == address(0)) revert InvalidAddress();

        toposCoreContract = IToposCoreContract(toposCoreContract_);
    }

    function execute(
        bytes calldata, /*certId*/
        bytes32 commandId,
        subnetId destinationSubnetId,
        address destinationContractAddress,
        bytes calldata payload
    ) external override {
        // if (_validateCallData(certId) == false) revert InvalidCallData();
        bytes32 payloadHash = keccak256(payload);
        if (
            !toposCoreContract.validateContractCall(
                commandId,
                destinationSubnetId,
                destinationContractAddress,
                payloadHash
            )
        ) revert NotApprovedByToposCoreContract();
        _execute(destinationSubnetId, destinationContractAddress, payload);
    }

    function executeWithToken(
        bytes calldata certId,
        bytes32 commandId,
        subnetId destinationSubnetId,
        address destinationContractAddress,
        bytes calldata payload,
        string calldata tokenSymbol,
        uint256 amount
    ) external override {
        if (_validateCallData(certId) == false) revert InvalidCallData();
        bytes32 payloadHash = keccak256(payload);
        if (
            !toposCoreContract.validateContractCallAndMint(
                commandId,
                destinationSubnetId,
                destinationContractAddress,
                payloadHash,
                tokenSymbol,
                amount
            )
        ) revert NotApprovedByToposCoreContract();

        _executeWithToken(destinationSubnetId, destinationContractAddress, payload, tokenSymbol, amount);
    }

    function _execute(
        subnetId destinationSubnetId,
        address destinationContractAddress,
        bytes calldata payload
    ) internal virtual {}

    function _executeWithToken(
        subnetId destinationSubnetId,
        address destinationContractAddress,
        bytes calldata payload,
        string calldata tokenSymbol,
        uint256 amount
    ) internal virtual {}

    function _validateCallData(bytes calldata certId) internal view returns (bool isOk) {
        isOk = true;
        bytes memory storedCert = toposCoreContract.getValidatedCert(certId);
        if (storedCert.length == 0) isOk = false;
    }

    function char(bytes1 b) internal pure returns (bytes1 c) {
        if (uint8(b) < 10) return bytes1(uint8(b) + 0x30);
        else return bytes1(uint8(b) + 0x57);
    }
}
