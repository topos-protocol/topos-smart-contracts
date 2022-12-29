// SPDX-License-Identifier: MIT
pragma solidity ^0.8.9;

type SubnetPublicKey is bytes32;

contract SubnetRegistrator {
    error SubnetAlreadyRegistered(SubnetPublicKey publicKey);
    error SubnetNotRegistered(SubnetPublicKey publicKey);

    struct Subnet {
        bytes endpoint;
        bytes logoURL;
        string name;
        string symbol;
        bool isPresent;
    }

    /// @notice Mapping to store the registered subnets
    /// @dev SubnetPublicKey => Subnet
    mapping(SubnetPublicKey => Subnet) public subnets;

    /// @notice New subnet registration event
    event NewSubnetRegistered(SubnetPublicKey publicKey);

    /// @notice Subnet removal event
    event SubnetRemoved(SubnetPublicKey publicKey);

    /// @notice Register a new subnet
    /// @param endpoint JSON RPC endpoint of a subnet
    /// @param logoURL URL for the logo of a subnet
    /// @param name name of a subnet
    /// @param publicKey FROST public key of a subnet
    /// @param symbol symbol for a subnet currency
    function registerSubnet(
        bytes calldata endpoint,
        bytes calldata logoURL,
        string calldata name,
        SubnetPublicKey publicKey,
        string calldata symbol
    ) public {
        if (subnets[publicKey].isPresent) revert SubnetAlreadyRegistered(publicKey);
        Subnet memory subnet = Subnet(endpoint, logoURL, name, symbol, true);
        subnets[publicKey] = subnet;
        emit NewSubnetRegistered(publicKey);
    }

    /// @notice Remove an already registered subnet
    /// @param publicKey FROST public key of a subnet
    function removeSubnet(SubnetPublicKey publicKey) public {
        if (!subnets[publicKey].isPresent) revert SubnetNotRegistered(publicKey);
        delete subnets[publicKey];
        emit SubnetRemoved(publicKey);
    }
}
