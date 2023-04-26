// SPDX-License-Identifier: MIT

pragma solidity ^0.8.9;

import {IMintableCappedERC20} from "./../interfaces/IMintableCappedERC20.sol";

import {ERC20} from "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import {ERC20Permit} from "./ERC20Permit.sol";
import {Ownable} from "./Ownable.sol";

contract MintableCappedERC20 is IMintableCappedERC20, ERC20, ERC20Permit, Ownable {
    uint256 public immutable cap;

    constructor(
        string memory name,
        string memory symbol,
        uint256 capacity,
        uint256 initialSupply,
        address deployer
    ) ERC20(name, symbol) ERC20Permit(name) Ownable() {
        if (capacity != 0 && initialSupply > capacity) revert CapExceeded();
        cap = capacity;
        _mint(deployer, initialSupply);
    }

    function mint(address account, uint256 amount) external onlyOwner {
        uint256 capacity = cap;

        _mint(account, amount);

        if (capacity == 0) return;

        if (totalSupply() > capacity) revert CapExceeded();
    }
}
