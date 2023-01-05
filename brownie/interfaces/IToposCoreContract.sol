// SPDX-License-Identifier: MIT
pragma solidity ^0.8.9;

type subnetId is bytes32; // type of subnet IDs

interface IToposCoreContract {
    /**********\
    |* Errors *|
    \**********/

    error CertNotPresent();
    error CertAlreadyPresent();
    error BurnFailed(string symbol);
    error ExceedDailyMintLimit(string symbol);
    error InvalidAmount();
    error InvalidCert();
    error InvalidCodeHash();
    error InvalidSetDailyMintLimitsParams();
    error InvalidSubnetId();
    error InvalidTokenDeployer();
    error MintFailed(string symbol);
    error NotProxy();
    error SetupFailed();
    error TokenAlreadyExists(string symbol);
    error TokenContractDoesNotExist(address token);
    error TokenDeployFailed(string symbol);
    error TokenDoesNotExist(string symbol);
    error TransferAlreadyExecuted();

    struct Certificate {
        bytes certId;
        uint256 position;
        bool isPresent;
    }

    /**********\
    |* Events *|
    \**********/

    event TokenSent(
        address indexed sender,
        subnetId sourceSubnetId,
        subnetId targetSubnetId,
        address receiver,
        string symbol,
        uint256 amount
    );

    event ContractCall(
        subnetId sourceSubnetId,
        address sourceContractAddr,
        subnetId targetSubnetId,
        address targetContractAddr,
        bytes32 indexed payloadHash,
        bytes payload
    );

    event ContractCallWithToken(
        subnetId sourceSubnetId,
        address sourceContractAddr,
        subnetId targetSubnetId,
        address targetContractAddr,
        bytes32 indexed payloadHash,
        bytes payload,
        string symbol,
        uint256 amount
    );

    event CertStored(bytes certId);

    event TokenDeployed(string symbol, address tokenAddresses);

    event TokenDailyMintLimitUpdated(string symbol, uint256 limit);

    event Upgraded(address indexed implementation);

    event ContractCallDataVerified(uint256 certPosition);

    /********************\
    |* Public Functions *|
    \********************/

    function sendToken(
        subnetId targetSubnetId,
        address receiver,
        string calldata symbol,
        uint256 amount
    ) external;

    function executeAssetTransfer(
        bytes calldata certId,
        bytes calldata crossSubnetTx,
        bytes calldata crossSubnetTxProof
    ) external;

    function callContract(
        subnetId targetSubnetId,
        address targetContractAddr,
        bytes calldata payload
    ) external;

    function callContractWithToken(
        subnetId targetSubnetId,
        address targetContractAddr,
        bytes calldata payload,
        string calldata symbol,
        uint256 amount
    ) external;

    function verifyContractCallData(bytes calldata certId, subnetId targetSubnetId) external returns (uint256);

    function deployToken(bytes calldata params) external;

    /***********\
    |* Getters *|
    \***********/

    function tokenDailyMintLimit(string memory symbol) external view returns (uint256);

    function tokenDailyMintAmount(string memory symbol) external view returns (uint256);

    function tokenAddresses(string memory symbol) external view returns (address);

    function implementation() external view returns (address);

    function adminEpoch() external view returns (uint256);

    function adminThreshold(uint256 epoch) external view returns (uint256);

    function admins(uint256 epoch) external view returns (address[] memory);

    function getStorageCert(bytes calldata certId) external view returns (Certificate memory);

    function tokenDeployer() external view returns (address);

    /*******************\
    |* Admin Functions *|
    \*******************/

    function setTokenDailyMintLimits(string[] calldata symbols, uint256[] calldata limits) external;

    function pushCertificate(bytes calldata certBytes) external;

    function giveToken(
        string memory symbol,
        address account,
        uint256 amount
    ) external;

    function upgrade(
        address newImplementation,
        bytes32 newImplementationCodeHash,
        bytes calldata setupParams
    ) external;

    /**********************\
    |* External Functions *|
    \**********************/

    function setup(bytes calldata params) external;
}
