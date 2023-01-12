// SPDX-License-Identifier: MIT
pragma solidity ^0.8.9;

import "./Bytes32Sets.sol";
type SubnetId is bytes32;

contract SubnetRegistrator {
    using Bytes32SetsLib for Bytes32SetsLib.Set;

    struct Subnet {
        string endpoint;
        string logoURL;
        string name;
        string currencySymbol;
    }

    /// @notice Set of subnet public keys
    Bytes32SetsLib.Set subnetSet;

    /// @notice Mapping to store the registered subnets
    /// @dev SubnetId => Subnet
    mapping(SubnetId => Subnet) public subnets;

    /// @notice New subnet registration event
    event NewSubnetRegistered(SubnetId publicKey);

    /// @notice Subnet removal event
    event SubnetRemoved(SubnetId publicKey);

    /// @notice Check if the subnet is already registered
    /// @param publicKey FROST public key of a subnet
    function subnetExists(SubnetId publicKey) external view returns (bool) {
        return subnetSet.exists(SubnetId.unwrap(publicKey));
    }

    /// @notice Gets the count of the registered subnets
    function getSubnetCount() external view returns (uint256) {
        return subnetSet.count();
    }

    /// @notice Register a new subnet
    /// @param endpoint JSON RPC endpoint of a subnet
    /// @param logoURL URL for the logo of a subnet
    /// @param name name of a subnet
    /// @param publicKey FROST public key of a subnet
    /// @param currencySymbol currencySymbol for a subnet currency
    function registerSubnet(
        string calldata endpoint,
        string calldata logoURL,
        string calldata name,
        SubnetId publicKey,
        string calldata currencySymbol
    ) public {
        subnetSet.insert(SubnetId.unwrap(publicKey));
        Subnet storage subnet = subnets[publicKey];
        subnet.endpoint = endpoint;
        subnet.logoURL = logoURL;
        subnet.name = name;
        subnet.currencySymbol = currencySymbol;
        emit NewSubnetRegistered(publicKey);
    }

    /// @notice Remove an already registered subnet
    /// @param publicKey FROST public key of a subnet
    function removeSubnet(SubnetId publicKey) public {
        subnetSet.remove(SubnetId.unwrap(publicKey));
        delete subnets[publicKey];
        emit SubnetRemoved(publicKey);
    }
}
