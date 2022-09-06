// SPDX-License-Identifier: MIT
pragma solidity ^0.8.2;

import "@openzeppelin/contracts-upgradeable/contracts/access/AccessControlUpgradeable.sol";
import "@openzeppelin/contracts-upgradeable/contracts/token/ERC20/ERC20Upgradeable.sol";
import "../interfaces/IAsset.sol";

contract Asset is ERC20Upgradeable, AccessControlUpgradeable {
    // 0xa95257aebefccffaada4758f028bce81ea992693be70592f620c4c9a0d9e715a
    bytes32 public constant VALIDATOR = keccak256(abi.encodePacked("VALIDATOR"));

    modifier onlyValidator() {
        require(hasRole(VALIDATOR, msg.sender), "onlyValidator: bad role");
        _;
    }

    function mint(address _receiver, uint256 _amount) external onlyValidator {
        // console.log("Asset.mint: Receiver %s, Sender %s", _receiver, msg.sender);
        _mint(_receiver, _amount);
    }

    function burn(address _account, uint256 _amount) external onlyValidator {
        _burn(_account, _amount);
    }

    function initialize(
        string memory _name,
        string memory _symbol,
        uint256 _initialSupply,
        address _deployer,
        address _validator
    ) public initializer {
        __ERC20_init(_name, _symbol);
        __AccessControl_init();
        _grantRole(DEFAULT_ADMIN_ROLE, _deployer);
        _grantRole(VALIDATOR, _validator);
        _mint(_deployer, _initialSupply);
    }
}
