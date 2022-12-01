// SPDX-License-Identifier: MIT

pragma solidity ^0.8.9;

import {CrossSubnetArbitraryCall} from "./CrossSubnetArbitraryCall.sol";

contract CrossSubnetArbitraryCallCreationCode {
    function getCreationBytecode(address toposCoreContract_) public pure returns (bytes memory) {
        bytes memory bytecode = type(CrossSubnetArbitraryCall).creationCode;

        return abi.encodePacked(bytecode, abi.encode(toposCoreContract_));
    }
}
