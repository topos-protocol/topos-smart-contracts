// SPDX-License-Identifier: MIT

pragma solidity ^0.8.9;

import {IOwnable} from "./IOwnable.sol";

interface IAuth is IOwnable {
    function validateProof(bytes32 messageHash, bytes calldata proof) external returns (bool currentOperators);

    function transferOperatorship(bytes calldata params) external;
}
