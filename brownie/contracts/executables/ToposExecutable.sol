// SPDX-License-Identifier: MIT

pragma solidity ^0.8.9;

import {IToposCoreContract, CertificateId, SubnetId} from "./../../interfaces/IToposCoreContract.sol";
import {IToposExecutable} from "./../../interfaces/IToposExecutable.sol";

contract ToposExecutable is IToposExecutable {
    IToposCoreContract public toposCoreContract;
    mapping(bytes32 => bool) private _boolStorage;
    mapping(bytes32 => uint256) private _uint256Storage;

    bytes32 internal constant PREFIX_ADMIN = keccak256("admin");
    bytes32 internal constant PREFIX_CONTRACT_CALL_EXECUTED = keccak256("contract-call-executed");
    bytes32 internal constant PREFIX_CONTRACT_CALL_EXECUTED_WITH_MINT = keccak256("contract-call-executed-with-mint");
    bytes32 internal constant PREFIX_AUTHORIZED_ORIGINS = keccak256("authorized-origins");

    modifier onlyAdmin() {
        if (!_isAdmin(msg.sender)) revert NotAdmin();
        _;
    }

    constructor(address toposCoreContract_) {
        if (toposCoreContract_ == address(0)) revert InvalidAddress();

        toposCoreContract = IToposCoreContract(toposCoreContract_);
        // deployer becomes admin
        _setAdmin(msg.sender);
    }

    function authorizeOrigin(
        SubnetId sourceSubnetId,
        address sourceContractAddr,
        bytes32 selector,
        uint256 minimumCertPosition
    ) external onlyAdmin {
        _setAuthorizedOrigin(sourceSubnetId, sourceContractAddr, selector, minimumCertPosition);
        emit OriginAuthorized(sourceSubnetId, sourceContractAddr, selector, minimumCertPosition);
    }

    function execute(
        CertificateId certId,
        ContractCallData memory contractCallData,
        bytes calldata /*crossSubnetTxProof*/
    ) external override {
        uint256 certPosition = toposCoreContract.verifyContractCallData(certId, contractCallData.targetSubnetId);
        if (_isContractCallExecuted(contractCallData) == true) revert ContractCallAlreadyExecuted();
        uint256 minimumCertPosition = _isAuthorizedOrigin(
            contractCallData.sourceSubnetId,
            contractCallData.sourceContractAddr,
            contractCallData.selector
        );
        if (certPosition <= minimumCertPosition) revert UnauthorizedOrigin();

        // prevent re-entrancy
        _setContractCallExecuted(contractCallData);
        _execute(
            contractCallData.targetSubnetId,
            contractCallData.targetContractAddr,
            contractCallData.selector,
            contractCallData.payload
        );
    }

    function executeWithToken(
        CertificateId certId,
        ContractCallWithTokenData memory contractCallWithTokenData,
        bytes calldata /*crossSubnetTxProof*/
    ) external override {
        uint256 certPosition = toposCoreContract.verifyContractCallData(
            certId,
            contractCallWithTokenData.targetSubnetId
        );
        if (_isContractCallAndMintExecuted(contractCallWithTokenData) == true) revert ContractCallAlreadyExecuted();
        uint256 minimumCertPosition = _isAuthorizedOrigin(
            contractCallWithTokenData.sourceSubnetId,
            contractCallWithTokenData.sourceContractAddr,
            contractCallWithTokenData.selector
        );
        if (certPosition <= minimumCertPosition) revert UnauthorizedOrigin();

        // prevent re-entrancy
        _setContractCallExecutedWithMint(contractCallWithTokenData);
        _executeWithToken(
            contractCallWithTokenData.targetSubnetId,
            contractCallWithTokenData.targetContractAddr,
            contractCallWithTokenData.selector,
            contractCallWithTokenData.payload,
            contractCallWithTokenData.symbol,
            contractCallWithTokenData.amount
        );
    }

    /// @dev only for testing set admin manually
    function setAdmin() external {
        _setAdmin(msg.sender);
    }

    function getBool(bytes32 key) public view returns (bool) {
        return _boolStorage[key];
    }

    function getUint256(bytes32 key) public view returns (uint256) {
        return _uint256Storage[key];
    }

    function _execute(
        SubnetId targetSubnetId,
        address targetContractAddr,
        bytes32 selector,
        bytes memory payload
    ) internal virtual {}

    function _executeWithToken(
        SubnetId targetSubnetId,
        address targetContractAddr,
        bytes32 selector,
        bytes memory payload,
        string memory tokenSymbol,
        uint256 amount
    ) internal virtual {}

    function _setBool(bytes32 key, bool value) internal {
        _boolStorage[key] = value;
    }

    function _setUint256(bytes32 key, uint256 value) internal {
        _uint256Storage[key] = value;
    }

    function _setAdmin(address adminAddr) internal {
        _setBool(_getAdminKey(adminAddr), true);
    }

    function _setContractCallExecuted(ContractCallData memory contractCallData) internal {
        _setBool(_getIsContractCallExecutedKey(contractCallData), true);
    }

    function _setContractCallExecutedWithMint(ContractCallWithTokenData memory contractCallWithTokenData) internal {
        _setBool(_getIsContractCallExecutedWithMintKey(contractCallWithTokenData), true);
    }

    function _setAuthorizedOrigin(
        SubnetId sourceSubnetId,
        address sourceContractAddr,
        bytes32 selector,
        uint256 minimumCertPosition
    ) internal {
        _setUint256(_getAuthorizedOriginsKey(sourceSubnetId, sourceContractAddr, selector), minimumCertPosition);
    }

    function _isAdmin(address account) internal view returns (bool) {
        return getBool(_getAdminKey(account));
    }

    function _isContractCallExecuted(ContractCallData memory contractCallData) internal view returns (bool) {
        return getBool(_getIsContractCallExecutedKey(contractCallData));
    }

    function _isContractCallAndMintExecuted(ContractCallWithTokenData memory contractCallWithTokenData)
        internal
        view
        returns (bool)
    {
        return getBool(_getIsContractCallExecutedWithMintKey(contractCallWithTokenData));
    }

    function _isAuthorizedOrigin(
        SubnetId sourceSubnetId,
        address sourceContractAddr,
        bytes32 selector
    ) internal view returns (uint256) {
        return getUint256(_getAuthorizedOriginsKey(sourceSubnetId, sourceContractAddr, selector));
    }

    function char(bytes1 b) internal pure returns (bytes1 c) {
        if (uint8(b) < 10) return bytes1(uint8(b) + 0x30);
        else return bytes1(uint8(b) + 0x57);
    }

    function _getIsContractCallExecutedKey(ContractCallData memory contractCallData) internal pure returns (bytes32) {
        return
            keccak256(
                abi.encode(
                    PREFIX_CONTRACT_CALL_EXECUTED,
                    contractCallData.txHash,
                    contractCallData.sourceSubnetId,
                    contractCallData.sourceContractAddr,
                    contractCallData.targetSubnetId,
                    contractCallData.targetContractAddr,
                    contractCallData.payloadHash,
                    contractCallData.payload,
                    contractCallData.selector
                )
            );
    }

    function _getIsContractCallExecutedWithMintKey(ContractCallWithTokenData memory contractCallWithTokenData)
        internal
        pure
        returns (bytes32)
    {
        return
            keccak256(
                abi.encode(
                    PREFIX_CONTRACT_CALL_EXECUTED_WITH_MINT,
                    contractCallWithTokenData.txHash,
                    contractCallWithTokenData.sourceSubnetId,
                    contractCallWithTokenData.sourceContractAddr,
                    contractCallWithTokenData.targetSubnetId,
                    contractCallWithTokenData.targetContractAddr,
                    contractCallWithTokenData.payloadHash,
                    contractCallWithTokenData.payload,
                    contractCallWithTokenData.symbol,
                    contractCallWithTokenData.amount,
                    contractCallWithTokenData.selector
                )
            );
    }

    function _getAdminKey(address adminAddr) internal pure returns (bytes32) {
        return keccak256(abi.encode(PREFIX_ADMIN, adminAddr));
    }

    function _getAuthorizedOriginsKey(
        SubnetId sourceSubnetId,
        address sourceContractAddr,
        bytes32 selector
    ) internal pure returns (bytes32) {
        return keccak256(abi.encode(PREFIX_AUTHORIZED_ORIGINS, sourceSubnetId, sourceContractAddr, selector));
    }
}
