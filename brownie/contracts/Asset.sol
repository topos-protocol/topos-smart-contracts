// SPDX-License-Identifier: MIT
pragma solidity ^0.8.2;

import "@openzeppelin/contracts-upgradeable/contracts/access/OwnableUpgradeable.sol";
import "@openzeppelin/contracts-upgradeable/contracts/token/ERC20/ERC20Upgradeable.sol";
import "../interfaces/IAsset.sol";

contract Asset is ERC20Upgradeable, OwnableUpgradeable {
    function mint(address _receiver, uint256 _amount) external onlyOwner {
        _mint(_receiver, _amount);
    }

    function burn(uint256 _amount) external onlyOwner {
        _burn(msg.sender, _amount);
    }

    function initialize(
        string memory _name,
        string memory _symbol,
        uint256 _initialSupply
    ) public initializer {
        __ERC20_init(_name, _symbol);
        _mint(msg.sender, _initialSupply);
    }
}
