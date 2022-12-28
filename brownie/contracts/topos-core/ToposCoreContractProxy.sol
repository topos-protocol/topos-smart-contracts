// SPDX-License-Identifier: MIT
pragma solidity ^0.8.9;

import {EternalStorage} from "./EternalStorage.sol";
import {IToposCoreContract, subnetId} from "./../../interfaces/IToposCoreContract.sol";

contract ToposCoreContractProxy is EternalStorage {
    error InvalidImplementation();
    error SetupFailed();
    error NativeCurrencyNotAccepted();

    /// @dev Storage slot with the address of the current factory. `keccak256('eip1967.proxy.implementation') - 1`.
    bytes32 internal constant KEY_IMPLEMENTATION =
        bytes32(0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc);

    constructor(address tccImplementation, bytes memory params) {
        if (tccImplementation.code.length == 0) revert InvalidImplementation();
        _setAddress(KEY_IMPLEMENTATION, tccImplementation);

        // solhint-disable-next-line avoid-low-level-calls
        (bool success, ) = tccImplementation.delegatecall(
            abi.encodeWithSelector(IToposCoreContract.setup.selector, params)
        );
        if (!success) revert SetupFailed();
    }

    // solhint-disable-next-line no-empty-blocks
    function setup(bytes calldata params) external {}

    // solhint-disable-next-line no-complex-fallback
    fallback() external payable {
        address implementation = getAddress(KEY_IMPLEMENTATION);

        // solhint-disable-next-line no-inline-assembly
        assembly {
            calldatacopy(0, 0, calldatasize())

            let result := delegatecall(gas(), implementation, 0, calldatasize(), 0, 0)

            returndatacopy(0, 0, returndatasize())

            switch result
            case 0 {
                revert(0, returndatasize())
            }
            default {
                return(0, returndatasize())
            }
        }
    }

    receive() external payable {
        revert NativeCurrencyNotAccepted();
    }
}
