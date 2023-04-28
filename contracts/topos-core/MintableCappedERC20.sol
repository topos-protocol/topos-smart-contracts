// SPDX-License-Identifier: MIT

pragma solidity ^0.8.9;

import {IMintableCappedERC20} from "./../interfaces/IMintableCappedERC20.sol";

import {ERC20} from "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import {ERC20Permit} from "./ERC20Permit.sol";
import {Ownable} from "./Ownable.sol";

contract MintableCappedERC20 is IMintableCappedERC20, ERC20, ERC20Permit, Ownable {
    uint256 public immutable cap;

    /// @notice Deploy a new instance of MintableCappedERC20
    /// @dev The deployer is the initial owner of the token
    /// @param name The name of the token
    /// @param symbol The symbol of the token
    /// @param capacity The maximum amount of tokens that can be minted
    /// @param initialSupply The initial amount of tokens to mint
    /// @param deployer The address of the token deployer
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
