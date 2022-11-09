// SPDX-License-Identifier: MIT

pragma solidity ^0.8.9;

import {ToposExecutable} from "./../ToposExecutable.sol";
import {subnetId} from "./../../../interfaces/IToposCoreContract.sol";
import {IERC20} from "./../../../interfaces/IERC20.sol";

contract CrossSubnetArbitraryCall is ToposExecutable {
    string public value;
    subnetId public destinationSubnetId_;
    address destinationContractAddress_;

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
        bytes memory payload
    ) internal override {
        (value) = abi.decode(payload, (string));
        destinationSubnetId_ = destinationSubnetId;
        destinationContractAddress_ = destinationContractAddress;
    }
}
