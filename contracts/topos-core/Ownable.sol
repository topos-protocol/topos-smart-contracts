// SPDX-License-Identifier: MIT

pragma solidity ^0.8.9;

import {IOwnable} from "./../interfaces/IOwnable.sol";

abstract contract Ownable is IOwnable {
    address public owner;

    modifier onlyOwner() {
        if (owner != msg.sender) revert NotOwner();

        _;
    }

    constructor() {
        owner = msg.sender;
        emit OwnershipTransferred(address(0), msg.sender);
    }

    function transferOwnership(address newOwner) external virtual onlyOwner {
        if (newOwner == address(0)) revert InvalidOwner();

        emit OwnershipTransferred(owner, newOwner);
        owner = newOwner;
    }
}
