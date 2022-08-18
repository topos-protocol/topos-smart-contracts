// SPDX-License-Identifier: MIT
pragma solidity ^0.8.2;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "../interfaces/IAsset.sol";

contract Asset is IAsset, ERC20 {
    constructor(
        string memory _name,
        string memory _symbol,
        uint256 _initialSupply
    ) ERC20(_name, _symbol) {
        _mint(msg.sender, _initialSupply);
    }

    function mint(address _receiver, uint256 _amount) external override {
        _mint(_receiver, _amount);
    }

    function burn(uint256 _amount) external override {
        _burn(msg.sender, _amount);
    }
}
