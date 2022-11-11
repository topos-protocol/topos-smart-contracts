// SPDX-License-Identifier: MIT

pragma solidity ^0.8.9;

import {ToposExecutable} from "./../ToposExecutable.sol";
import {subnetId} from "./../../../interfaces/IToposCoreContract.sol";
import {IERC20} from "./../../../interfaces/IERC20.sol";

contract CrossSubnetArbitraryCall is ToposExecutable {
    error UnknownSelector();

    string public value;
    subnetId public destinationSubnetId_;
    address destinationContractAddress_;

    bytes32 internal constant SELECTOR_CHANGE_VALUE = keccak256("changeValue");

    constructor(address toposCoreContract_) ToposExecutable(toposCoreContract_) {}

    // Call this function to update the value of this contract along with all its siblings'.
    function setRemoteValue(
        subnetId destinationSubnetId,
        address destinationContractAddress,
        string calldata value_
    ) external payable {
        bytes memory payload = abi.encode(value_);
        toposCoreContract.callContract(destinationSubnetId, destinationContractAddress, payload);
    }

    // Handles calls created by setAndSend. Updates this contract's value
    function _execute(
        subnetId destinationSubnetId,
        address destinationContractAddress,
        bytes32 selector,
        bytes memory payload
    ) internal override {
        if (selector == SELECTOR_CHANGE_VALUE) {
            destinationSubnetId_ = destinationSubnetId;
            destinationContractAddress_ = destinationContractAddress;
            changeValue(payload);
        } else {
            revert UnknownSelector();
        }
    }

    function changeValue(bytes memory payload) internal {
        value = abi.decode(payload, (string));
    }
}
