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
        uint256 chainId;
    }

    /// @notice Set of subnet IDs
    Bytes32SetsLib.Set subnetSet;

    /// @notice Mapping to store the registered subnets
    /// @dev SubnetId => Subnet
    mapping(SubnetId => Subnet) public subnets;

    /// @notice New subnet registration event
    event NewSubnetRegistered(SubnetId subnetId);

    /// @notice Subnet removal event
    event SubnetRemoved(SubnetId subnetId);

    /// @notice Check if the subnet is already registered
    /// @param subnetId FROST public key of a subnet
    function subnetExists(SubnetId subnetId) external view returns (bool) {
        return subnetSet.exists(SubnetId.unwrap(subnetId));
    }

    /// @notice Gets the count of the registered subnets
    function getSubnetCount() external view returns (uint256) {
        return subnetSet.count();
    }

    /// @notice Gets the subnet Id at the provided Index
    /// @param index index at which the Subnet ID is stored
    function getSubnetIdAtIndex(uint256 index) external view returns (SubnetId) {
        return SubnetId.wrap(subnetSet.keyAtIndex(index));
    }

    /// @notice Register a new subnet
    /// @param endpoint JSON RPC endpoint of a subnet
    /// @param logoURL URL for the logo of a subnet
    /// @param name name of a subnet
    /// @param subnetId FROST public key of a subnet
    /// @param currencySymbol currencySymbol for a subnet currency
    /// @param chainId subnet network ID
    function registerSubnet(
        string calldata endpoint,
        string calldata logoURL,
        string calldata name,
        SubnetId subnetId,
        string calldata currencySymbol,
        uint256 chainId
    ) public {
        subnetSet.insert(SubnetId.unwrap(subnetId));
        Subnet storage subnet = subnets[subnetId];
        subnet.endpoint = endpoint;
        subnet.logoURL = logoURL;
        subnet.name = name;
        subnet.currencySymbol = currencySymbol;
        subnet.chainId = chainId;
        emit NewSubnetRegistered(subnetId);
    }

    /// @notice Remove an already registered subnet
    /// @param subnetId FROST public key of a subnet
    function removeSubnet(SubnetId subnetId) public {
        subnetSet.remove(SubnetId.unwrap(subnetId));
        delete subnets[subnetId];
        emit SubnetRemoved(subnetId);
    }
}
