// SPDX-License-Identifier: MIT
pragma solidity ^0.8.9;

contract CodeHash {
    function getCodeHash(address targetContract) public view returns (bytes32) {
        if (targetContract.codehash.length != 0) {
            return targetContract.codehash;
        }
    }
}
