// SPDX-License-Identifier: MIT
pragma solidity ^0.8.9;

type subnetId is bytes32; // type of subnet IDs

interface IToposCoreContract {
    /**********\
    |* Errors *|
    \**********/

    error NotSelf();
    error NotProxy();
    error InvalidCodeHash();
    error SetupFailed();
    error InvalidAuthModule();
    error InvalidTokenDeployer();
    error InvalidAmount();
    error InvalidChainId();
    error InvalidCommands();
    error TokenDoesNotExist(string symbol);
    error TokenAlreadyExists(string symbol);
    error TokenDeployFailed(string symbol);
    error TokenContractDoesNotExist(address token);
    error BurnFailed(string symbol);
    error MintFailed(string symbol);
    error InvalidSetDailyMintLimitsParams();
    error ExceedDailyMintLimit(string symbol);
    error InvalidCallData();

    /**********\
    |* Events *|
    \**********/

    event TokenSent(
        address indexed sender,
        subnetId destinationSubnetId,
        address receiver,
        string symbol,
        uint256 amount
    );

    event ContractCall(
        address indexed sender,
        subnetId destinationSubnetId,
        address destinationContractAddress,
        bytes32 indexed payloadHash,
        bytes payload
    );

    event ContractCallWithToken(
        address indexed sender,
        subnetId destinationSubnetId,
        address destinationContractAddress,
        bytes32 indexed payloadHash,
        bytes payload,
        string symbol,
        uint256 amount
    );

    event Executed(bytes32 indexed commandId);

    event TokenDeployed(string symbol, address tokenAddresses);

    event ContractCallApproved(
        bytes32 indexed commandId,
        subnetId destinationSubnetId,
        address destinationContractAddress,
        address indexed sender,
        bytes32 indexed payloadHash,
        bytes32 sourceTxHash,
        uint256 sourceEventIndex
    );

    event ContractCallApprovedWithMint(
        bytes32 indexed commandId,
        subnetId destinationSubnetId,
        address destinationContractAddress,
        address indexed sender,
        bytes32 indexed payloadHash,
        string symbol,
        uint256 amount,
        bytes32 sourceTxHash,
        uint256 sourceEventIndex
    );

    event TokenDailyMintLimitUpdated(string symbol, uint256 limit);

    event OperatorshipTransferred(bytes newOperatorsData);

    event Upgraded(address indexed implementation);

    /********************\
    |* Public Functions *|
    \********************/

    function sendToken(
        subnetId destinationSubnetId,
        address destinationContractAddress,
        string calldata symbol,
        uint256 amount
    ) external;

    function callContract(
        subnetId destinationSubnetId,
        address destinationContractAddress,
        bytes calldata payload
    ) external;

    function callContractWithToken(
        subnetId destinationSubnetId,
        address destinationContractAddress,
        bytes calldata payload,
        string calldata symbol,
        uint256 amount
    ) external;

    function isContractCallApproved(
        bytes32 commandId,
        subnetId destinationSubnetId,
        address destinationContractAddress,
        address contractAddress,
        bytes32 payloadHash
    ) external view returns (bool);

    function isContractCallAndMintApproved(
        bytes32 commandId,
        subnetId destinationSubnetId,
        address destinationContractAddress,
        address contractAddress,
        bytes32 payloadHash,
        string calldata symbol,
        uint256 amount
    ) external view returns (bool);

    function validateContractCall(
        bytes32 commandId,
        subnetId destinationSubnetId,
        address destinationContractAddress,
        bytes32 payloadHash
    ) external returns (bool);

    function validateContractCallAndMint(
        bytes32 commandId,
        subnetId destinationSubnetId,
        address destinationContractAddress,
        bytes32 payloadHash,
        string calldata symbol,
        uint256 amount
    ) external returns (bool);

    /***********\
    |* Getters *|
    \***********/

    function tokenDailyMintLimit(string memory symbol) external view returns (uint256);

    function tokenDailyMintAmount(string memory symbol) external view returns (uint256);

    function allTokensFrozen() external view returns (bool);

    function implementation() external view returns (address);

    function tokenAddresses(string memory symbol) external view returns (address);

    function tokenFrozen(string memory symbol) external view returns (bool);

    function isCommandExecuted(bytes32 commandId) external view returns (bool);

    function adminEpoch() external view returns (uint256);

    function adminThreshold(uint256 epoch) external view returns (uint256);

    function admins(uint256 epoch) external view returns (address[] memory);

    function getValidatedCert(bytes calldata certId) external view returns (bytes memory);

    /*******************\
    |* Admin Functions *|
    \*******************/

    function setTokenDailyMintLimits(string[] calldata symbols, uint256[] calldata limits) external;

    function upgrade(
        address newImplementation,
        bytes32 newImplementationCodeHash,
        bytes calldata setupParams
    ) external;

    function verifyCertificate(bytes calldata cert) external;

    function approveContractCall(bytes calldata params, bytes32 commandId) external;

    function approveContractCallWithMint(bytes calldata params, bytes32 commandId) external;

    /**********************\
    |* External Functions *|
    \**********************/

    function setup(bytes calldata params) external;

    function execute(bytes calldata input) external;
}
