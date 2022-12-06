// SPDX-License-Identifier: MIT

pragma solidity ^0.8.9;

import {ToposExecutable} from "./../ToposExecutable.sol";
import {subnetId} from "./../../../interfaces/IToposCoreContract.sol";
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";

contract CrossSubnetArbitraryCall is ToposExecutable {
    error UnknownSelector();

    string public value;
    subnetId public targetSubnetId_;
    address targetContractAddr_;

    bytes32 internal constant SELECTOR_CHANGE_VALUE = keccak256("changeValue");

    constructor(address toposCoreContract_) ToposExecutable(toposCoreContract_) {}

    // Call this function to update the value of this contract along with all its siblings'.
    function setRemoteValue(
        subnetId targetSubnetId,
        address targetContractAddr,
        string calldata value_
    ) external payable {
        bytes memory payload = abi.encode(value_);
        toposCoreContract.callContract(targetSubnetId, targetContractAddr, payload);
    }

    // Handles calls created by setAndSend. Updates this contract's value
    function _execute(
        subnetId targetSubnetId,
        address targetContractAddr,
        bytes32 selector,
        bytes memory payload
    ) internal override {
        if (selector == SELECTOR_CHANGE_VALUE) {
            targetSubnetId_ = targetSubnetId;
            targetContractAddr_ = targetContractAddr;
            changeValue(payload);
        } else {
            revert UnknownSelector();
        }
    }

    function changeValue(bytes memory payload) internal {
        value = abi.decode(payload, (string));
    }
}
