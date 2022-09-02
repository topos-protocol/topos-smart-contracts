// SPDX-License-Identifier: MIT
pragma solidity ^0.8.2;

import "@openzeppelin/contracts-upgradeable/contracts/token/ERC20/IERC20Upgradeable.sol";

interface IAsset is IERC20Upgradeable {
    function mint(address _receiver, uint256 _amount) external;

    function burn(uint256 _amount) external;
}
