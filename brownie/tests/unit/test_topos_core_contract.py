import brownie
import eth_abi

import const as c


def test_push_certificate_reverts_on_already_stored_certificate(
    admin, topos_core_contract_A
):
    push_dummy_cert(admin, topos_core_contract_A)
    with brownie.reverts():
        # retry pushing the same cert
        push_dummy_cert(admin, topos_core_contract_A)


def test_push_certificate_emits_event(admin, topos_core_contract_A):
    tx = push_dummy_cert(admin, topos_core_contract_A)
    assert tx.events["CertStored"].values() == [c.CERT_BYTES]


def test_set_token_daily_mint_limits_reverts_on_mismatch_symbol_length(
    admin, topos_core_contract_A
):
    # symbol and limit array lenghts should be 1:1 ratio
    symbols = [c.TOKEN_SYMBOL_X, c.TOKEN_SYMBOL_Y]
    mint_limits = [c.MINT_AMOUNT]
    with brownie.reverts():
        topos_core_contract_A.setTokenDailyMintLimits(
            symbols, mint_limits, {"from": admin}
        )


def test_set_token_daily_mint_limits_reverts_on_token_does_not_exist(
    admin, topos_core_contract_A
):
    symbols = [c.TOKEN_SYMBOL_X]
    mint_limits = [c.MINT_AMOUNT]
    # should fail because token not deployed yet
    with brownie.reverts():
        topos_core_contract_A.setTokenDailyMintLimits(
            symbols, mint_limits, {"from": admin}
        )


def test_set_token_daily_mint_limits_emits_event(admin, topos_core_contract_A):
    symbols = [c.TOKEN_SYMBOL_X]
    mint_limits = [c.MINT_AMOUNT]
    topos_core_contract_A.deployToken(
        get_default_internal_token_val(), {"from": admin}
    )
    tx = topos_core_contract_A.setTokenDailyMintLimits(
        symbols, mint_limits, {"from": admin}
    )
    assert tx.events["TokenDailyMintLimitUpdated"].values() == [
        c.TOKEN_SYMBOL_X,
        c.MINT_AMOUNT,
    ]


def test_set_token_daily_mint_limits_allow_zero_limit(
    admin, alice, bob, topos_core_contract_A
):
    # token to be deployed args
    token_values = [
        c.TOKEN_NAME,
        c.TOKEN_SYMBOL_X,
        c.MINT_CAP,
        brownie.ZERO_ADDRESS,
        0,  # 0 daily mint limit = unlimited mint limit
    ]
    encoded_token_params = eth_abi.encode(c.TOKEN_PARAMS, token_values)
    topos_core_contract_A.deployToken(encoded_token_params, {"from": admin})
    push_dummy_cert(admin, topos_core_contract_A)
    tx = topos_core_contract_A.executeAssetTransfer(
        c.CERT_ID,
        get_default_mint_val(alice, bob),
        c.DUMMY_DATA,
        {"from": admin},
    )
    # the transaction should go through even without a daily mint limit set
    assert tx.events["Transfer"].values() == [
        brownie.ZERO_ADDRESS,
        bob.address,
        c.SEND_AMOUNT,
    ]


def test_deploy_token_reverts_on_token_already_deployed(
    admin, topos_core_contract_A
):
    topos_core_contract_A.deployToken(
        get_default_internal_token_val(), {"from": admin}
    )
    # retry deploying the same token
    with brownie.reverts():
        topos_core_contract_A.deployToken(
            get_default_internal_token_val(), {"from": admin}
        )


def test_deploy_token_external_token_emits_events(
    admin, topos_core_contract_A, BurnableMintableCappedERC20
):
    # deploy an external erc20 token
    burn_mint_erc20 = BurnableMintableCappedERC20.deploy(
        c.TOKEN_NAME, c.TOKEN_SYMBOL_X, c.MINT_CAP, {"from": admin}
    )
    tx = topos_core_contract_A.deployToken(
        get_default_external_token_val(burn_mint_erc20.address),
        {"from": admin},
    )
    assert tx.events["TokenDeployed"].values() == [
        c.TOKEN_SYMBOL_X,
        burn_mint_erc20.address,
    ]


def test_deploy_token_emits_events(admin, topos_core_contract_A):
    tx = topos_core_contract_A.deployToken(
        get_default_internal_token_val(), {"from": admin}
    )
    token_address = tx.events["TokenDeployed"]["tokenAddresses"]
    assert tx.events["TokenDailyMintLimitUpdated"].values() == [
        c.TOKEN_SYMBOL_X,
        c.DAILY_MINT_LIMIT,
    ]
    assert tx.events["TokenDeployed"].values() == [
        c.TOKEN_SYMBOL_X,
        token_address,
    ]


def test_setup_reverts_on_mismatch_admin_threshold(
    admin, TokenDeployer, ToposCoreContract, ToposCoreContractProxy
):
    new_admin_values = [[admin.address], 2]
    encoded_admin_params = eth_abi.encode(c.ADMIN_PARAMS, new_admin_values)
    topos_core_contract_impl = deploy_new_tcc(
        admin, TokenDeployer, ToposCoreContract
    )
    # should revert no. of admin address does not match the threshold
    with brownie.reverts():
        # `setup()` is part of the ToposCoreContractProxy constructor
        ToposCoreContractProxy.deploy(
            topos_core_contract_impl.address,
            encoded_admin_params,
            {"from": admin},
        )


def test_setup_reverts_on_admin_threshold_cannot_be_zero(
    admin, TokenDeployer, ToposCoreContract, ToposCoreContractProxy
):
    new_admin_values = [[admin.address], 0]
    encoded_admin_params = eth_abi.encode(c.ADMIN_PARAMS, new_admin_values)
    topos_core_contract_impl = deploy_new_tcc(
        admin, TokenDeployer, ToposCoreContract
    )
    # should revert since the threshold can't be zero
    with brownie.reverts():
        # `setup()` is part of the ToposCoreContractProxy constructor
        ToposCoreContractProxy.deploy(
            topos_core_contract_impl.address,
            encoded_admin_params,
            {"from": admin},
        )


def test_setup_reverts_on_duplicate_admin(
    admin, TokenDeployer, ToposCoreContract, ToposCoreContractProxy
):
    new_admin_values = [[admin.address, admin.address], 2]
    encoded_admin_params = eth_abi.encode(c.ADMIN_PARAMS, new_admin_values)
    topos_core_contract_impl = deploy_new_tcc(
        admin, TokenDeployer, ToposCoreContract
    )
    # should revert since you can't have two admins with the same address
    with brownie.reverts():
        # `setup()` is part of the ToposCoreContractProxy constructor
        ToposCoreContractProxy.deploy(
            topos_core_contract_impl.address,
            encoded_admin_params,
            {"from": admin},
        )


def test_setup_reverts_on_zero_address_admin(
    admin, TokenDeployer, ToposCoreContract, ToposCoreContractProxy
):
    new_admin_values = [[brownie.ZERO_ADDRESS], 1]
    encoded_admin_params = eth_abi.encode(c.ADMIN_PARAMS, new_admin_values)
    topos_core_contract_impl = deploy_new_tcc(
        admin, TokenDeployer, ToposCoreContract
    )
    # should revert since the admin address can't be zero address
    with brownie.reverts():
        # `setup()` is part of the ToposCoreContractProxy constructor
        ToposCoreContractProxy.deploy(
            topos_core_contract_impl.address,
            encoded_admin_params,
            {"from": admin},
        )


def test_setup_should_revert_on_non_proxy_call(
    admin,
    TokenDeployer,
    ToposCoreContract,
):
    admin_values = [[admin.address], 1]
    encoded_admin_params = eth_abi.encode(c.ADMIN_PARAMS, admin_values)
    topos_core_contract_impl = deploy_new_tcc(
        admin, TokenDeployer, ToposCoreContract
    )
    # should revert since delegate setup() cannot be called without proxy
    with brownie.reverts():
        topos_core_contract_impl.setup(
            encoded_admin_params,
            {"from": admin},
        )


def test_execute_transfer_reverts_on_unknown_cert(
    admin, alice, bob, topos_core_contract_A
):
    # should revert since the certificate is not present
    with brownie.reverts():
        topos_core_contract_A.executeAssetTransfer(
            c.CERT_ID,
            get_default_mint_val(alice, bob),
            c.DUMMY_DATA,
            {"from": admin},
        )


def test_execute_transfer_reverts_on_invalid_subnet_id(
    admin, alice, bob, topos_core_contract_A
):
    # default target subnet id is set to "0x01"
    dummy_target_subnet_id = brownie.convert.to_bytes("0x02", "bytes32")
    push_dummy_cert(admin, topos_core_contract_A)
    # execute asset transfer args
    mint_token_values = [
        c.DUMMY_DATA,
        alice.address,
        c.SOURCE_SUBNET_ID,
        dummy_target_subnet_id,
        bob.address,
        c.TOKEN_SYMBOL_X,
        c.SEND_AMOUNT,
    ]
    encoded_mint_token_params = eth_abi.encode(
        c.MINT_TOKEN_PARAMS, mint_token_values
    )
    # should fail since the provided target subnet id is different
    with brownie.reverts():
        topos_core_contract_A.executeAssetTransfer(
            c.CERT_ID, encoded_mint_token_params, c.DUMMY_DATA, {"from": admin}
        )


def test_execute_transfer_reverts_on_call_already_executed(
    admin, alice, bob, topos_core_contract_A
):
    topos_core_contract_A.deployToken(
        get_default_internal_token_val(), {"from": admin}
    )
    push_dummy_cert(admin, topos_core_contract_A)
    topos_core_contract_A.executeAssetTransfer(
        c.CERT_ID,
        get_default_mint_val(alice, bob),
        c.DUMMY_DATA,
        {"from": admin},
    )
    # resending the same call should fail
    with brownie.reverts():
        topos_core_contract_A.executeAssetTransfer(
            c.CERT_ID,
            get_default_mint_val(alice, bob),
            c.DUMMY_DATA,
            {"from": admin},
        )


def test_execute_transfer_reverts_on_token_does_not_exist(
    admin, alice, bob, topos_core_contract_A
):
    dummy_token_symbol = "DUMMY"
    topos_core_contract_A.deployToken(
        get_default_internal_token_val(), {"from": admin}
    )
    push_dummy_cert(admin, topos_core_contract_A)
    # execute asset transfer args
    mint_token_values = [
        c.DUMMY_DATA,
        alice.address,
        c.SOURCE_SUBNET_ID,
        c.SOURCE_SUBNET_ID,
        bob.address,
        dummy_token_symbol,
        c.SEND_AMOUNT,
    ]
    encoded_mint_token_params = eth_abi.encode(
        c.MINT_TOKEN_PARAMS, mint_token_values
    )
    # should fail since the dummy token wasn't deployed on ToposCoreContract
    with brownie.reverts():
        topos_core_contract_A.executeAssetTransfer(
            c.CERT_ID, encoded_mint_token_params, c.DUMMY_DATA, {"from": admin}
        )


def test_execute_transfer_reverts_on_exceeding_daily_mint_limit(
    admin, alice, bob, topos_core_contract_A
):
    send_amount = 110
    topos_core_contract_A.deployToken(
        get_default_internal_token_val(), {"from": admin}
    )
    push_dummy_cert(admin, topos_core_contract_A)
    # execute asset transfer args
    mint_token_values = [
        c.DUMMY_DATA,
        alice.address,
        c.SOURCE_SUBNET_ID,
        c.SOURCE_SUBNET_ID,
        bob.address,
        c.TOKEN_SYMBOL_X,
        send_amount,
    ]
    encoded_mint_token_params = eth_abi.encode(
        c.MINT_TOKEN_PARAMS, mint_token_values
    )
    # should fail since the send_amount is greater than DAILY_MINT_LIMIT
    with brownie.reverts():
        topos_core_contract_A.executeAssetTransfer(
            c.CERT_ID, encoded_mint_token_params, c.DUMMY_DATA, {"from": admin}
        )


def test_execute_transfer_reverts_on_external_cannot_mint_to_zero_address(
    admin,
    alice,
    topos_core_contract_A,
    BurnableMintableCappedERC20,
):
    # deploy an external erc20 token
    burn_mint_erc20 = BurnableMintableCappedERC20.deploy(
        c.TOKEN_NAME, c.TOKEN_SYMBOL_X, c.MINT_CAP, {"from": admin}
    )
    # register the external token on ToposCoreContract
    topos_core_contract_A.deployToken(
        get_default_external_token_val(burn_mint_erc20.address),
        {"from": admin},
    )

    # mint amount for ToposCoreContract
    burn_mint_erc20.mint(
        topos_core_contract_A.address,
        c.MINT_AMOUNT,
        {"from": admin},
    )
    push_dummy_cert(admin, topos_core_contract_A)
    # execute asset transfer args
    mint_token_values = [
        c.DUMMY_DATA,
        alice.address,
        c.SOURCE_SUBNET_ID,
        c.SOURCE_SUBNET_ID,
        brownie.ZERO_ADDRESS,  # receiver is zero address
        c.TOKEN_SYMBOL_X,
        c.SEND_AMOUNT,
    ]
    encoded_mint_token_params = eth_abi.encode(
        c.MINT_TOKEN_PARAMS, mint_token_values
    )
    # should revert since the receiver address cannot be zero address
    with brownie.reverts():
        topos_core_contract_A.executeAssetTransfer(
            c.CERT_ID, encoded_mint_token_params, c.DUMMY_DATA, {"from": admin}
        )


def test_execute_transfer_external_token_transfer_emits_events(
    admin,
    alice,
    bob,
    topos_core_contract_A,
    BurnableMintableCappedERC20,
):
    # deploy an external erc20 token
    burn_mint_erc20 = BurnableMintableCappedERC20.deploy(
        c.TOKEN_NAME, c.TOKEN_SYMBOL_X, c.MINT_CAP, {"from": admin}
    )
    # register the external token on ToposCoreContract
    topos_core_contract_A.deployToken(
        get_default_external_token_val(burn_mint_erc20.address),
        {"from": admin},
    )
    # mint amount for ToposCoreContract
    burn_mint_erc20.mint(
        topos_core_contract_A.address,
        c.MINT_AMOUNT,
        {"from": admin},
    )
    push_dummy_cert(admin, topos_core_contract_A)
    tx = topos_core_contract_A.executeAssetTransfer(
        c.CERT_ID,
        get_default_mint_val(alice, bob),
        c.DUMMY_DATA,
        {"from": admin},
    )
    assert tx.events["Transfer"].values() == [
        topos_core_contract_A.address,
        bob.address,
        c.SEND_AMOUNT,
    ]


def test_execute_transfer_emits_event(
    admin, alice, bob, topos_core_contract_A
):
    topos_core_contract_A.deployToken(
        get_default_internal_token_val(), {"from": admin}
    )
    push_dummy_cert(admin, topos_core_contract_A)
    tx = topos_core_contract_A.executeAssetTransfer(
        c.CERT_ID,
        get_default_mint_val(alice, bob),
        c.DUMMY_DATA,
        {"from": admin},
    )
    assert tx.events["Transfer"].values() == [
        brownie.ZERO_ADDRESS,
        bob.address,
        c.SEND_AMOUNT,
    ]


def test_send_token_reverts_on_token_does_not_exist(
    admin,
    alice,
    bob,
    topos_core_contract_A,
    BurnableMintableCappedERC20,
):
    dummy_token_symbol = "DUMMY"
    tx = topos_core_contract_A.deployToken(
        get_default_internal_token_val(), {"from": admin}
    )
    topos_core_contract_A.giveToken(
        c.TOKEN_SYMBOL_X, alice, c.MINT_AMOUNT, {"from": admin}
    )
    burnable_mint_erc20 = BurnableMintableCappedERC20.at(
        tx.events["TokenDeployed"]["tokenAddresses"]
    )
    burnable_mint_erc20.approve(
        topos_core_contract_A, c.APPROVE_AMOUNT, {"from": alice}
    )
    # should revert since the dummy token wasn't deployed on ToposCoreContract
    with brownie.reverts():
        topos_core_contract_A.sendToken(
            c.TARGET_SUBNET_ID,
            bob,
            dummy_token_symbol,
            c.SEND_AMOUNT,
            {"from": alice},
        )


def test_send_token_reverts_on_zero_amount(
    admin,
    alice,
    bob,
    topos_core_contract_A,
    BurnableMintableCappedERC20,
):
    send_amount = 0
    tx = topos_core_contract_A.deployToken(
        get_default_internal_token_val(), {"from": admin}
    )
    topos_core_contract_A.giveToken(
        c.TOKEN_SYMBOL_X, alice, c.MINT_AMOUNT, {"from": admin}
    )
    burnable_mint_erc20 = BurnableMintableCappedERC20.at(
        tx.events["TokenDeployed"]["tokenAddresses"]
    )
    burnable_mint_erc20.approve(
        topos_core_contract_A, c.APPROVE_AMOUNT, {"from": alice}
    )
    # should revert since zero amount cannot be minted
    with brownie.reverts():
        topos_core_contract_A.sendToken(
            c.TARGET_SUBNET_ID,
            bob,
            c.TOKEN_SYMBOL_X,
            send_amount,
            {"from": alice},
        )


def test_send_token_reverts_on_external_token_burn_fail(
    admin,
    alice,
    bob,
    topos_core_contract_A,
    BurnableMintableCappedERC20,
):
    # deploy an external erc20 token
    burn_mint_erc20 = BurnableMintableCappedERC20.deploy(
        c.TOKEN_NAME, c.TOKEN_SYMBOL_X, c.MINT_CAP, {"from": admin}
    )
    # register the token onto ToposCoreContract
    topos_core_contract_A.deployToken(
        get_default_external_token_val(burn_mint_erc20.address),
        {"from": admin},
    )
    # should fail because alice does not have enough balance to burn
    with brownie.reverts():
        topos_core_contract_A.sendToken(
            c.TARGET_SUBNET_ID,
            bob,
            c.TOKEN_SYMBOL_X,
            c.SEND_AMOUNT,
            {"from": alice},
        )


def test_send_token_external_token_emits_events(
    admin,
    alice,
    bob,
    topos_core_contract_A,
    BurnableMintableCappedERC20,
):
    # deploy an external erc20 token
    burn_mint_erc20 = BurnableMintableCappedERC20.deploy(
        c.TOKEN_NAME, c.TOKEN_SYMBOL_X, c.MINT_CAP, {"from": admin}
    )
    burn_mint_erc20.mint(alice, c.MINT_AMOUNT, {"from": admin})
    approve_tx = burn_mint_erc20.approve(
        topos_core_contract_A, c.APPROVE_AMOUNT, {"from": alice}
    )
    assert approve_tx.events["Approval"].values() == [
        alice,
        topos_core_contract_A.address,
        c.SEND_AMOUNT,
    ]
    # register the token onto ToposCoreContract
    topos_core_contract_A.deployToken(
        get_default_external_token_val(burn_mint_erc20.address),
        {"from": admin},
    )
    send_token_tx = topos_core_contract_A.sendToken(
        c.TARGET_SUBNET_ID,
        bob,
        c.TOKEN_SYMBOL_X,
        c.SEND_AMOUNT,
        {"from": alice},
    )
    assert send_token_tx.events["Transfer"].values() == [
        alice,
        topos_core_contract_A.address,
        c.SEND_AMOUNT,
    ]
    assert send_token_tx.events["TokenSent"].values() == [
        alice.address,
        brownie.convert.datatypes.HexString(c.SOURCE_SUBNET_ID, "bytes32"),
        brownie.convert.datatypes.HexString(c.TARGET_SUBNET_ID, "bytes32"),
        bob.address,
        c.TOKEN_SYMBOL_X,
        c.SEND_AMOUNT,
    ]


def test_send_token_reverts_on_burn_fail(
    admin, alice, bob, topos_core_contract_A
):
    topos_core_contract_A.deployToken(
        get_default_internal_token_val(), {"from": admin}
    )
    # should fail because alice does not have enough balance to burn
    with brownie.reverts():
        topos_core_contract_A.sendToken(
            c.TARGET_SUBNET_ID,
            bob,
            c.TOKEN_SYMBOL_X,
            c.SEND_AMOUNT,
            {"from": alice},
        )


def test_send_token_emits_events(
    admin,
    alice,
    bob,
    topos_core_contract_A,
    BurnableMintableCappedERC20,
):
    tx = topos_core_contract_A.deployToken(
        get_default_internal_token_val(), {"from": admin}
    )
    topos_core_contract_A.giveToken(
        c.TOKEN_SYMBOL_X, alice, c.MINT_AMOUNT, {"from": admin}
    )
    burnable_mint_erc20 = BurnableMintableCappedERC20.at(
        tx.events["TokenDeployed"]["tokenAddresses"]
    )
    approve_tx = burnable_mint_erc20.approve(
        topos_core_contract_A, c.APPROVE_AMOUNT, {"from": alice}
    )
    assert approve_tx.events["Approval"].values() == [
        alice,
        topos_core_contract_A.address,
        c.SEND_AMOUNT,
    ]
    send_token_tx = topos_core_contract_A.sendToken(
        c.TARGET_SUBNET_ID,
        bob,
        c.TOKEN_SYMBOL_X,
        c.SEND_AMOUNT,
        {"from": alice},
    )
    assert send_token_tx.events["Transfer"].values() == [
        alice,
        brownie.ZERO_ADDRESS,
        c.SEND_AMOUNT,
    ]
    assert send_token_tx.events["TokenSent"].values() == [
        alice.address,
        brownie.convert.datatypes.HexString(c.SOURCE_SUBNET_ID, "bytes32"),
        brownie.convert.datatypes.HexString(c.TARGET_SUBNET_ID, "bytes32"),
        bob.address,
        c.TOKEN_SYMBOL_X,
        c.SEND_AMOUNT,
    ]


def test_call_contract_emits_event(accounts, alice, topos_core_contract_A):
    target_contract_addr = accounts.add()
    tx = topos_core_contract_A.callContract(
        c.TARGET_SUBNET_ID,
        target_contract_addr,
        c.DUMMY_DATA,
        {"from": alice},
    )
    assert tx.events["ContractCall"].values() == [
        brownie.convert.datatypes.HexString(c.SOURCE_SUBNET_ID, "bytes32"),
        alice.address,
        brownie.convert.datatypes.HexString(c.TARGET_SUBNET_ID, "bytes32"),
        target_contract_addr.address,
        brownie.convert.datatypes.HexString(c.DUMMY_DATA, "bytes"),
    ]


def test_call_contract_with_token_emits_event(
    accounts,
    admin,
    alice,
    topos_core_contract_A,
    BurnableMintableCappedERC20,
):
    tx = topos_core_contract_A.deployToken(
        get_default_internal_token_val(), {"from": admin}
    )
    topos_core_contract_A.giveToken(
        c.TOKEN_SYMBOL_X, alice, c.MINT_AMOUNT, {"from": admin}
    )
    burnable_mint_erc20 = BurnableMintableCappedERC20.at(
        tx.events["TokenDeployed"]["tokenAddresses"]
    )
    burnable_mint_erc20.approve(
        topos_core_contract_A, c.APPROVE_AMOUNT, {"from": alice}
    )
    target_contract_addr = accounts.add()
    tx = topos_core_contract_A.callContractWithToken(
        c.TARGET_SUBNET_ID,
        target_contract_addr,
        c.DUMMY_DATA,
        c.TOKEN_SYMBOL_X,
        c.SEND_AMOUNT,
        {"from": alice},
    )
    assert tx.events["ContractCallWithToken"].values() == [
        brownie.convert.datatypes.HexString(c.SOURCE_SUBNET_ID, "bytes32"),
        alice.address,
        brownie.convert.datatypes.HexString(c.TARGET_SUBNET_ID, "bytes32"),
        target_contract_addr.address,
        brownie.convert.datatypes.HexString(c.DUMMY_DATA, "bytes"),
        c.TOKEN_SYMBOL_X,
        c.SEND_AMOUNT,
    ]


def test_verify_contract_call_data_reverts_on_cert_not_present(
    admin, topos_core_contract_A
):
    fixture_subnet_id = c.SOURCE_SUBNET_ID
    # should fail since the certificate is not present
    with brownie.reverts():
        topos_core_contract_A.verifyContractCallData(
            c.CERT_ID, fixture_subnet_id, {"from": admin}
        )


def test_verify_contract_call_data_reverts_on_unidentified_subnet_id(
    admin, topos_core_contract_A
):
    fixture_subnet_id = c.TARGET_SUBNET_ID
    push_dummy_cert(admin, topos_core_contract_A)
    # should revert since fixture is set to source_subnet_id
    with brownie.reverts():
        topos_core_contract_A.verifyContractCallData(
            c.CERT_ID, fixture_subnet_id, {"from": admin}
        )


def test_verify_contract_call_returns_cert_position(
    admin, topos_core_contract_A
):
    fixture_subnet_id = c.SOURCE_SUBNET_ID
    push_dummy_cert(admin, topos_core_contract_A)
    tx = topos_core_contract_A.verifyContractCallData(
        c.CERT_ID, fixture_subnet_id, {"from": admin}
    )
    assert (
        tx.events["ContractCallDataVerified"]["certPosition"]
        == c.CERT_POSITION
    )


def test_upgrade_emits_event(
    admin, topos_core_contract_A, CodeHash, TokenDeployer, ToposCoreContract
):
    admin_values = [[admin.address], 1]
    encoded_admin_params = eth_abi.encode(c.ADMIN_PARAMS, admin_values)
    topos_core_contract_impl = deploy_new_tcc(
        admin, TokenDeployer, ToposCoreContract
    )
    # verify that the current delegate is not the same as the new delegate
    assert (
        topos_core_contract_A.implementation({"from": admin})
        != topos_core_contract_impl.address
    )
    code_hash = CodeHash.deploy({"from": admin})
    codehash = code_hash.getCodeHash(topos_core_contract_impl.address)
    tx = topos_core_contract_A.upgrade(
        topos_core_contract_impl.address,
        codehash,
        encoded_admin_params,
        {"from": admin},
    )
    # the proxy storage should point to the new delegate address
    assert (
        tx.events["Upgraded"]["implementation"]
        == topos_core_contract_impl.address
    )


# internal functions #
def push_dummy_cert(admin, topos_core_contract_A):
    return topos_core_contract_A.pushCertificate(
        eth_abi.encode(["bytes", "uint256"], [c.CERT_ID, c.CERT_POSITION]),
        {"from": admin},
    )


def get_default_internal_token_val():
    token_values = [
        c.TOKEN_NAME,
        c.TOKEN_SYMBOL_X,
        c.MINT_CAP,
        brownie.ZERO_ADDRESS,  # address zero since not yet deployed
        c.DAILY_MINT_LIMIT,
    ]
    return eth_abi.encode(c.TOKEN_PARAMS, token_values)


def get_default_external_token_val(address):
    token_values = [
        c.TOKEN_NAME,
        c.TOKEN_SYMBOL_X,
        c.MINT_CAP,
        address,  # specify deployed token address
        c.DAILY_MINT_LIMIT,
    ]
    return eth_abi.encode(c.TOKEN_PARAMS, token_values)


def get_default_mint_val(alice, bob):
    mint_token_args = [
        c.DUMMY_DATA,
        alice.address,
        c.SOURCE_SUBNET_ID,
        c.SOURCE_SUBNET_ID,
        bob.address,
        c.TOKEN_SYMBOL_X,
        c.SEND_AMOUNT,
    ]
    return eth_abi.encode(c.MINT_TOKEN_PARAMS, mint_token_args)


def deploy_new_tcc(admin, TokenDeployer, ToposCoreContract):
    token_deployer = TokenDeployer.deploy({"from": admin})
    return ToposCoreContract.deploy(
        token_deployer.address, c.SOURCE_SUBNET_ID, {"from": admin}
    )
