// SPDX-License-Identifier: MIT
pragma solidity ^0.8.9;

type subnetId is bytes32; // type of subnet IDs

interface IToposCoreContract {
    /**********\
    |* Errors *|
    \**********/

    error InvalidTokenDeployer();
    error InvalidAmount();
    error TokenDoesNotExist(string symbol);
    error TokenAlreadyExists(string symbol);
    error TokenDeployFailed(string symbol);
    error TokenContractDoesNotExist(address token);
    error BurnFailed(string symbol);
    error MintFailed(string symbol);
    error InvalidSetDailyMintLimitsParams();
    error ExceedDailyMintLimit(string symbol);
    error CertNotVerified();
    error CertAlreadyVerified();
    error InvalidCert();
    error InvalidSubnetId();
    error TransferAlreadyExecuted();

    struct Certificate {
        bytes certId;
        uint256 position;
        bool isVerified;
    }

    /**********\
    |* Events *|
    \**********/

    event TokenSent(
        address indexed sender,
        subnetId originSubnetId,
        subnetId destinationSubnetId,
        address receiver,
        string symbol,
        uint256 amount
    );

    event ContractCall(
        subnetId originSubnetId,
        address originAddress,
        subnetId destinationSubnetId,
        address destinationContractAddress,
        bytes32 indexed payloadHash,
        bytes payload
    );

    event ContractCallWithToken(
        subnetId originSubnetId,
        address originAddress,
        subnetId destinationSubnetId,
        address destinationContractAddress,
        bytes32 indexed payloadHash,
        bytes payload,
        string symbol,
        uint256 amount
    );

    event CertVerified(bytes certId);

    event TokenDeployed(string symbol, address tokenAddresses);

    event TokenDailyMintLimitUpdated(string symbol, uint256 limit);

    /********************\
    |* Public Functions *|
    \********************/

    function sendToken(
        subnetId destinationSubnetId,
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

    function verifyContractCallData(bytes calldata certId, subnetId destinationSubnetId) external returns (uint256);

    /***********\
    |* Getters *|
    \***********/

    function tokenDailyMintLimit(string memory symbol) external view returns (uint256);

    function tokenDailyMintAmount(string memory symbol) external view returns (uint256);

    function tokenAddresses(string memory symbol) external view returns (address);

    function adminEpoch() external view returns (uint256);

    function adminThreshold(uint256 epoch) external view returns (uint256);

    function admins(uint256 epoch) external view returns (address[] memory);

    function getVerfiedCert(bytes calldata certId) external view returns (Certificate memory);

    /*******************\
    |* Admin Functions *|
    \*******************/

    function setTokenDailyMintLimits(string[] calldata symbols, uint256[] calldata limits) external;

    function verifyCertificate(bytes calldata certBytes) external;

    function giveToken(
        string memory symbol,
        address account,
        uint256 amount
    ) external;

    /**********************\
    |* External Functions *|
    \**********************/

    function setup(bytes calldata params) external;
}
