// SPDX-License-Identifier: MIT
pragma solidity ^0.8.2;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "../interfaces/IAsset.sol";

/// @title Asset
/// @notice Standard ERC20 token
contract Asset is IAsset, ERC20 {
    /// @notice Constructor
    /// @dev Mints the initial supply for the deployer
    /// @param _name Name of the token
    /// @param _symbol Symbol of the token
    /// @param _initialSupply Initial amount to mint
    constructor(
        string memory _name,
        string memory _symbol,
        uint256 _initialSupply
    ) ERC20(_name, _symbol) {
        _mint(msg.sender, _initialSupply);
    }

    /// @notice Mint a custom amount for the caller
    /// @dev Overrides the parent external function
    /// @param _receiver Address of the receiver
    /// @param _amount Amount to mint
    function mint(address _receiver, uint256 _amount) external override {
        _mint(_receiver, _amount);
    }

    /// @notice Burn a custom amount from the caller
    /// @dev Overrides the parent external function
    /// @param _amount Amount to burn
    function burn(uint256 _amount) external override {
        _burn(msg.sender, _amount);
    }
}
