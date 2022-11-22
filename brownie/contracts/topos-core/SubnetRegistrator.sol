// SPDX-License-Identifier: MIT
pragma solidity ^0.8.9;

contract SubnetRegistrator {
    error SubnetAlreadyRegistered(bytes publicKey);

    struct Subnet {
        bytes endpoint;
        bytes logoURL;
        string name;
        bool isPresent;
    }

    /// @notice Mapping to store the registered subnets
    /// @dev publicKey => Subnet
    mapping(bytes => Subnet) subnets;

    /// @notice New subnet registration event
    event NewSubnetRegistered(bytes publicKey);

    /// @notice Register a new subnet
    /// @param endpoint JSON RPC endpoint of a subnet
    /// @param logoURL URL for the logo of a subnet
    /// @param name name of a subnet
    /// @param publicKey FROST public key of a subnet
    function registerSubnet(
        bytes calldata endpoint,
        bytes calldata logoURL,
        string calldata name,
        bytes calldata publicKey
    ) public {
        if (subnets[publicKey].isPresent) revert SubnetAlreadyRegistered(publicKey);
        Subnet memory subnet = Subnet(endpoint, logoURL, name, true);
        subnets[publicKey] = subnet;
        emit NewSubnetRegistered(publicKey);
    }
}
