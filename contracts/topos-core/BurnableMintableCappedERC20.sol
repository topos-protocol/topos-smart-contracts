// SPDX-License-Identifier: MIT

pragma solidity ^0.8.9;

import {IBurnableMintableCappedERC20} from "./../interfaces/IBurnableMintableCappedERC20.sol";

import {MintableCappedERC20} from "./MintableCappedERC20.sol";
import {DepositHandler} from "./DepositHandler.sol";

contract BurnableMintableCappedERC20 is IBurnableMintableCappedERC20, MintableCappedERC20 {
    constructor(
        string memory name,
        string memory symbol,
        uint256 capacity,
        uint256 initialSupply,
        address deployer,
        address operator
    ) MintableCappedERC20(name, symbol, capacity, initialSupply, deployer, operator) {}

    function burn(bytes32 salt) external {
        require(
            hasRole(DEFAULT_ADMIN_ROLE, msg.sender) || hasRole(OPERATOR_ROLE, msg.sender),
            "BurnableMintableCappedERC20: must have the admin or operator role to burn"
        );
        address account = depositAddress(salt);
        _burn(account, balanceOf(account));
    }

    function burnFrom(address account, uint256 amount) external {
        require(
            hasRole(DEFAULT_ADMIN_ROLE, msg.sender) || hasRole(OPERATOR_ROLE, msg.sender),
            "BurnableMintableCappedERC20: must have the admin or operator role to burn"
        );
        uint256 _allowance = allowance(account, msg.sender);
        if (_allowance != type(uint256).max) {
            _approve(account, msg.sender, _allowance - amount);
        }
        _burn(account, amount);
    }

    function depositAddress(bytes32 salt) public view returns (address) {
        /* Convert a hash which is bytes32 to an address which is 20-byte long
        according to https://docs.soliditylang.org/en/v0.8.1/control-structures.html?highlight=create2#salted-contract-creations-create2 */
        // TODO: remove unused code
        // return
        //     address(
        //         uint160(
        //             uint256(
        //                 keccak256(
        //                     abi.encodePacked(
        //                         bytes1(0xff),
        //                         owner,
        //                         salt,
        //                         keccak256(abi.encodePacked(type(DepositHandler).creationCode))
        //                     )
        //                 )
        //             )
        //         )
        //     );
    }
}
