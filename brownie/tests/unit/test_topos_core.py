import brownie
from Crypto.Hash import keccak
from eth_abi import encode
from eth_abi.packed import encode_abi_packed

import const as c


def test_push_certificate_reverts_on_already_stored_certificate(
    admin, topos_core_A
):
    push_dummy_cert(admin, topos_core_A)
    with brownie.reverts():
        # retry pushing the same cert
        push_dummy_cert(admin, topos_core_A)


def test_get_certificate_count_returns_count(admin, topos_core_A):
    count = 1
    push_dummy_cert(admin, topos_core_A)
    assert topos_core_A.getCertificateCount({"from": admin}) == count


def test_push_certificate_emits_event(admin, topos_core_A):
    tx = push_dummy_cert(admin, topos_core_A)
    assert topos_core_A.certificateExists(c.CERT_ID, {"from": admin}) is True
    assert tx.events["CertStored"].values() == [
        c.CERT_BYTES,
        brownie.convert.datatypes.HexString(c.TX_ROOT, "bytes32"),
    ]


def test_get_cert_id_at_index_returns_cert_id(admin, topos_core_A):
    index = 0  # only one imported certificate
    push_dummy_cert(admin, topos_core_A)
    assert (
        topos_core_A.getCertIdAtIndex(index, {"from": admin}) == c.CERT_BYTES
    )


def test_get_token_count_returns_count(admin, topos_core_A):
    count = 1
    topos_core_A.deployToken(get_default_internal_token_val(), {"from": admin})
    assert topos_core_A.getTokenCount({"from": admin}) == count


def test_get_token_count_for_multiple_returns_count(admin, topos_core_A):
    count = 2
    topos_core_A.deployToken(get_default_internal_token_val(), {"from": admin})
    topos_core_A.deployToken(
        get_secondary_internal_token_val(), {"from": admin}
    )
    assert topos_core_A.getTokenCount({"from": admin}) == count


def test_get_token_key_at_index_returns_token_key_hash(admin, topos_core_A):
    index = 0  # only one deployed token
    topos_core_A.deployToken(get_default_internal_token_val(), {"from": admin})
    token_key_hash = get_token_key_hash(c.TOKEN_SYMBOL_X)
    assert (
        topos_core_A.getTokenKeyAtIndex(index, {"from": admin})
        == token_key_hash
    )


def test_get_checkpoints_returns_single_checkpoint(admin, topos_core_A):
    push_dummy_cert(admin, topos_core_A)
    checkpoints = topos_core_A.getCheckpoints({"from": admin})
    assert checkpoints[0] == (
        brownie.convert.datatypes.HexString(c.CERT_ID, "bytes32"),
        c.CERT_POSITION,
    )


def test_get_checkpoints_returns_multiple_checkpoints(admin, topos_core_A):
    test_certs = [
        (c.CERT_ID, c.SOURCE_SUBNET_ID, c.CERT_POSITION),
        (c.CERT_ID_2, c.SOURCE_SUBNET_ID_2, c.CERT_POSITION_2),
        (c.CERT_ID_3, c.SOURCE_SUBNET_ID_3, c.CERT_POSITION_3),
    ]
    for test_cert in test_certs:
        push_cert(
            admin, topos_core_A, test_cert[0], test_cert[1], test_cert[2]
        )
    checkpoints = topos_core_A.getCheckpoints({"from": admin})
    test_checkpoints = [
        (
            brownie.convert.datatypes.HexString(test_cert[0], "bytes32"),
            test_cert[2],
        )
        for test_cert in test_certs
    ]
    assert checkpoints == test_checkpoints


def test_get_token_key_at_index_for_multiple_returns_token_key_hash(
    admin, topos_core_A
):
    index = 0  # default token
    index_1 = 1  # second token
    topos_core_A.deployToken(get_default_internal_token_val(), {"from": admin})
    topos_core_A.deployToken(
        get_secondary_internal_token_val(), {"from": admin}
    )
    token_key_hash = get_token_key_hash(c.TOKEN_SYMBOL_X)
    token_key_hash_second = get_token_key_hash(c.TOKEN_SYMBOL_Y)

    assert (
        topos_core_A.getTokenKeyAtIndex(index, {"from": admin})
        == token_key_hash
    )
    assert (
        topos_core_A.getTokenKeyAtIndex(index_1, {"from": admin})
        == token_key_hash_second
    )


def test_get_token_by_key_returns_token(admin, topos_core_A):
    index = 0  # only one deployed token
    tx = topos_core_A.deployToken(
        get_default_internal_token_val(), {"from": admin}
    )
    token_address = tx.events["TokenDeployed"]["tokenAddress"]
    token_key_hash = topos_core_A.getTokenKeyAtIndex(index, {"from": admin})
    assert topos_core_A.tokens(token_key_hash, {"from": admin}) == [
        c.TOKEN_SYMBOL_X,
        token_address,
    ]


def test_set_token_daily_mint_limits_reverts_on_mismatch_symbol_length(
    admin, topos_core_A
):
    # symbol and limit array lengths should be 1:1 ratio
    symbols = [c.TOKEN_SYMBOL_X, c.TOKEN_SYMBOL_Y]
    mint_limits = [c.MINT_AMOUNT]
    with brownie.reverts():
        topos_core_A.setTokenDailyMintLimits(
            symbols, mint_limits, {"from": admin}
        )


def test_set_token_daily_mint_limits_reverts_on_token_does_not_exist(
    admin, topos_core_A
):
    symbols = [c.TOKEN_SYMBOL_X]
    mint_limits = [c.MINT_AMOUNT]
    # should fail because token not deployed yet
    with brownie.reverts():
        topos_core_A.setTokenDailyMintLimits(
            symbols, mint_limits, {"from": admin}
        )


def test_set_token_daily_mint_limits_emits_event(admin, topos_core_A):
    symbols = [c.TOKEN_SYMBOL_X]
    mint_limits = [c.MINT_AMOUNT]
    topos_core_A.deployToken(get_default_internal_token_val(), {"from": admin})
    tx = topos_core_A.setTokenDailyMintLimits(
        symbols, mint_limits, {"from": admin}
    )
    assert tx.events["TokenDailyMintLimitUpdated"].values() == [
        c.TOKEN_SYMBOL_X,
        c.MINT_AMOUNT,
    ]


def test_set_token_daily_mint_limits_allow_zero_limit(
    admin, bob, topos_core_B
):
    # token to be deployed args
    token_values = [
        c.TOKEN_NAME,
        c.TOKEN_SYMBOL_X,
        c.MINT_CAP,
        brownie.ZERO_ADDRESS,
        0,  # 0 daily mint limit = unlimited mint limit
    ]
    encoded_token_params = encode(c.TOKEN_PARAMS, token_values)
    topos_core_B.deployToken(encoded_token_params, {"from": admin})
    push_dummy_cert(admin, topos_core_B)
    tx = topos_core_B.executeAssetTransfer(
        c.TX_ROOT,
        c.INDEX_OF_DATA_IN_TX_RAW,
        c.TX_RAW,
        c.DUMMY_DATA,
        {"from": admin},
    )
    # the transaction should go through even without a daily mint limit set
    assert tx.events["Transfer"].values() == [
        brownie.ZERO_ADDRESS,
        bob.address,
        c.SEND_AMOUNT,
    ]


def test_deploy_token_reverts_on_token_already_deployed(admin, topos_core_A):
    count = 1  # only one instance of a token deployed at once
    index = 0
    topos_core_A.deployToken(get_default_internal_token_val(), {"from": admin})
    # retry deploying the same token
    with brownie.reverts():
        topos_core_A.deployToken(
            get_default_internal_token_val(), {"from": admin}
        )
    assert topos_core_A.getTokenCount({"from": admin}) == count
    token_key_hash = get_token_key_hash(c.TOKEN_SYMBOL_X)
    assert (
        topos_core_A.getTokenKeyAtIndex(index, {"from": admin})
        == token_key_hash
    )


def test_deploy_token_external_token_emits_events(
    admin, topos_core_A, BurnableMintableCappedERC20
):
    # deploy an external erc20 token
    burn_mint_erc20 = BurnableMintableCappedERC20.deploy(
        c.TOKEN_NAME, c.TOKEN_SYMBOL_X, c.MINT_CAP, {"from": admin}
    )
    tx = topos_core_A.deployToken(
        get_default_external_token_val(burn_mint_erc20.address),
        {"from": admin},
    )
    assert tx.events["TokenDeployed"].values() == [
        c.TOKEN_SYMBOL_X,
        burn_mint_erc20.address,
    ]


def test_deploy_token_emits_events(admin, topos_core_A):
    tx = topos_core_A.deployToken(
        get_default_internal_token_val(), {"from": admin}
    )
    token_address = tx.events["TokenDeployed"]["tokenAddress"]
    assert tx.events["TokenDailyMintLimitUpdated"].values() == [
        c.TOKEN_SYMBOL_X,
        c.DAILY_MINT_LIMIT,
    ]
    assert tx.events["TokenDeployed"].values() == [
        c.TOKEN_SYMBOL_X,
        token_address,
    ]


def test_setup_reverts_on_mismatch_admin_threshold(
    admin, TokenDeployer, ToposCore, ToposCoreProxy
):
    new_admin_values = [[admin.address], 2]
    encoded_admin_params = encode(c.ADMIN_PARAMS, new_admin_values)
    topos_core_impl = deploy_new_tcc(admin, TokenDeployer, ToposCore)
    # should revert no. of admin address does not match the threshold
    with brownie.reverts():
        # `setup()` is part of the ToposCoreProxy constructor
        ToposCoreProxy.deploy(
            topos_core_impl.address,
            encoded_admin_params,
            {"from": admin},
        )


def test_setup_reverts_on_admin_threshold_cannot_be_zero(
    admin, TokenDeployer, ToposCore, ToposCoreProxy
):
    new_admin_values = [[admin.address], 0]
    encoded_admin_params = encode(c.ADMIN_PARAMS, new_admin_values)
    topos_core_impl = deploy_new_tcc(admin, TokenDeployer, ToposCore)
    # should revert since the threshold can't be zero
    with brownie.reverts():
        # `setup()` is part of the ToposCoreProxy constructor
        ToposCoreProxy.deploy(
            topos_core_impl.address,
            encoded_admin_params,
            {"from": admin},
        )


def test_setup_reverts_on_duplicate_admin(
    admin, TokenDeployer, ToposCore, ToposCoreProxy
):
    new_admin_values = [[admin.address, admin.address], 2]
    encoded_admin_params = encode(c.ADMIN_PARAMS, new_admin_values)
    topos_core_impl = deploy_new_tcc(admin, TokenDeployer, ToposCore)
    # should revert since you can't have two admins with the same address
    with brownie.reverts():
        # `setup()` is part of the ToposCoreProxy constructor
        ToposCoreProxy.deploy(
            topos_core_impl.address,
            encoded_admin_params,
            {"from": admin},
        )


def test_setup_reverts_on_zero_address_admin(
    admin, TokenDeployer, ToposCore, ToposCoreProxy
):
    new_admin_values = [[brownie.ZERO_ADDRESS], 1]
    encoded_admin_params = encode(c.ADMIN_PARAMS, new_admin_values)
    topos_core_impl = deploy_new_tcc(admin, TokenDeployer, ToposCore)
    # should revert since the admin address can't be zero address
    with brownie.reverts():
        # `setup()` is part of the ToposCoreProxy constructor
        ToposCoreProxy.deploy(
            topos_core_impl.address,
            encoded_admin_params,
            {"from": admin},
        )


def test_setup_should_revert_on_non_proxy_call(
    admin,
    TokenDeployer,
    ToposCore,
):
    admin_values = [[admin.address], 1]
    encoded_admin_params = encode(c.ADMIN_PARAMS, admin_values)
    topos_core_impl = deploy_new_tcc(admin, TokenDeployer, ToposCore)
    # should revert since delegate setup() cannot be called without proxy
    with brownie.reverts():
        topos_core_impl.setup(
            encoded_admin_params,
            {"from": admin},
        )


def test_execute_transfer_reverts_on_tx_raw_index_out_of_bounds(
    admin, topos_core_B
):
    topos_core_B.deployToken(get_default_internal_token_val(), {"from": admin})
    push_dummy_cert(admin, topos_core_B)
    # should revert since the index is out of bounds
    with brownie.reverts():
        topos_core_B.executeAssetTransfer(
            c.TX_ROOT,
            c.INDEX_OF_DATA_IN_TX_RAW_OUT_OF_BOUNDS,
            c.TX_RAW,
            c.DUMMY_DATA,
            {"from": admin},
        )


def test_execute_transfer_reverts_on_unknown_cert(admin, topos_core_B):
    # should revert since the certificate is not present
    with brownie.reverts():
        topos_core_B.executeAssetTransfer(
            c.CERT_ID,
            c.INDEX_OF_DATA_IN_TX_RAW,
            c.TX_RAW,
            c.DUMMY_DATA,
            {"from": admin},
        )


def test_execute_transfer_reverts_on_invalid_subnet_id(admin, topos_core_A):
    # subnet id of topos_core_A = "0x01"
    push_dummy_cert(admin, topos_core_A)
    # should fail since the provided target subnet id is not "0x02"
    with brownie.reverts():
        topos_core_A.executeAssetTransfer(
            c.TX_ROOT,
            c.INDEX_OF_DATA_IN_TX_RAW,
            c.TX_RAW,
            c.DUMMY_DATA,
            {"from": admin},
        )


def test_execute_transfer_reverts_on_call_already_executed(
    admin, topos_core_B
):
    topos_core_B.deployToken(get_default_internal_token_val(), {"from": admin})
    push_dummy_cert(admin, topos_core_B)
    topos_core_B.executeAssetTransfer(
        c.TX_ROOT,
        c.INDEX_OF_DATA_IN_TX_RAW,
        c.TX_RAW,
        c.DUMMY_DATA,
        {"from": admin},
    )
    # resending the same call should fail
    with brownie.reverts():
        topos_core_B.executeAssetTransfer(
            c.TX_ROOT,
            c.INDEX_OF_DATA_IN_TX_RAW,
            c.TX_RAW,
            c.DUMMY_DATA,
            {"from": admin},
        )


def test_execute_transfer_reverts_on_token_does_not_exist(admin, topos_core_B):
    push_dummy_cert(admin, topos_core_B)
    # should fail since the dummy token wasn't deployed on ToposCore
    with brownie.reverts():
        topos_core_B.executeAssetTransfer(
            c.TX_ROOT,
            c.INDEX_OF_DATA_IN_TX_RAW,
            c.TX_RAW,
            c.DUMMY_DATA,
            {"from": admin},
        )


def test_execute_transfer_reverts_on_exceeding_daily_mint_limit(
    admin, topos_core_B
):
    topos_core_B.deployToken(get_default_internal_token_val(), {"from": admin})
    push_dummy_cert(admin, topos_core_B)
    # should fail since the send_amount is greater than DAILY_MINT_LIMIT
    with brownie.reverts():
        topos_core_B.executeAssetTransfer(
            c.TX_ROOT,
            c.INDEX_OF_DATA_IN_TX_RAW,
            c.TX_RAW_MINT_EXCEED,
            c.DUMMY_DATA,
            {"from": admin},
        )


def test_execute_transfer_reverts_on_external_cannot_mint_to_zero_address(
    admin,
    topos_core_B,
    BurnableMintableCappedERC20,
):
    # deploy an external erc20 token
    burn_mint_erc20 = BurnableMintableCappedERC20.deploy(
        c.TOKEN_NAME, c.TOKEN_SYMBOL_X, c.MINT_CAP, {"from": admin}
    )
    # register the external token on ToposCore
    topos_core_B.deployToken(
        get_default_external_token_val(burn_mint_erc20.address),
        {"from": admin},
    )

    # mint amount for ToposCore
    burn_mint_erc20.mint(
        topos_core_B.address,
        c.MINT_AMOUNT,
        {"from": admin},
    )
    push_dummy_cert(admin, topos_core_B)
    # should revert since the receiver address cannot be zero address
    with brownie.reverts():
        topos_core_B.executeAssetTransfer(
            c.TX_ROOT,
            c.INDEX_OF_DATA_IN_TX_RAW,
            c.TX_RAW_ZERO_ADDRESS,
            c.DUMMY_DATA,
            {"from": admin},
        )


def test_execute_transfer_external_token_transfer_emits_events(
    admin,
    bob,
    topos_core_B,
    BurnableMintableCappedERC20,
):
    # deploy an external erc20 token
    burn_mint_erc20 = BurnableMintableCappedERC20.deploy(
        c.TOKEN_NAME, c.TOKEN_SYMBOL_X, c.MINT_CAP, {"from": admin}
    )
    # register the external token on ToposCore
    topos_core_B.deployToken(
        get_default_external_token_val(burn_mint_erc20.address),
        {"from": admin},
    )
    # mint amount for ToposCore
    burn_mint_erc20.mint(
        topos_core_B.address,
        c.MINT_AMOUNT,
        {"from": admin},
    )
    push_dummy_cert(admin, topos_core_B)
    tx = topos_core_B.executeAssetTransfer(
        c.TX_ROOT,
        c.INDEX_OF_DATA_IN_TX_RAW,
        c.TX_RAW,
        c.DUMMY_DATA,
        {"from": admin},
    )
    assert tx.events["Transfer"].values() == [
        topos_core_B.address,
        bob.address,
        c.SEND_AMOUNT,
    ]


def test_execute_transfer_emits_event(admin, bob, topos_core_B):
    topos_core_B.deployToken(get_default_internal_token_val(), {"from": admin})
    push_dummy_cert(admin, topos_core_B)
    tx = topos_core_B.executeAssetTransfer(
        c.TX_ROOT,
        c.INDEX_OF_DATA_IN_TX_RAW,
        c.TX_RAW,
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
    topos_core_A,
    BurnableMintableCappedERC20,
):
    dummy_token_symbol = "DUMMY"
    tx = topos_core_A.deployToken(
        get_default_internal_token_val(), {"from": admin}
    )
    topos_core_A.giveToken(
        c.TOKEN_SYMBOL_X, alice, c.MINT_AMOUNT, {"from": admin}
    )
    burnable_mint_erc20 = BurnableMintableCappedERC20.at(
        tx.events["TokenDeployed"]["tokenAddress"]
    )
    burnable_mint_erc20.approve(
        topos_core_A, c.APPROVE_AMOUNT, {"from": alice}
    )
    # should revert since the dummy token wasn't deployed on ToposCore
    with brownie.reverts():
        topos_core_A.sendToken(
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
    topos_core_A,
    BurnableMintableCappedERC20,
):
    send_amount = 0
    tx = topos_core_A.deployToken(
        get_default_internal_token_val(), {"from": admin}
    )
    topos_core_A.giveToken(
        c.TOKEN_SYMBOL_X, alice, c.MINT_AMOUNT, {"from": admin}
    )
    burnable_mint_erc20 = BurnableMintableCappedERC20.at(
        tx.events["TokenDeployed"]["tokenAddress"]
    )
    burnable_mint_erc20.approve(
        topos_core_A, c.APPROVE_AMOUNT, {"from": alice}
    )
    # should revert since zero amount cannot be minted
    with brownie.reverts():
        topos_core_A.sendToken(
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
    topos_core_A,
    BurnableMintableCappedERC20,
):
    # deploy an external erc20 token
    burn_mint_erc20 = BurnableMintableCappedERC20.deploy(
        c.TOKEN_NAME, c.TOKEN_SYMBOL_X, c.MINT_CAP, {"from": admin}
    )
    # register the token onto ToposCore
    topos_core_A.deployToken(
        get_default_external_token_val(burn_mint_erc20.address),
        {"from": admin},
    )
    # should fail because alice does not have enough balance to burn
    with brownie.reverts():
        topos_core_A.sendToken(
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
    topos_core_A,
    BurnableMintableCappedERC20,
):
    # deploy an external erc20 token
    burn_mint_erc20 = BurnableMintableCappedERC20.deploy(
        c.TOKEN_NAME, c.TOKEN_SYMBOL_X, c.MINT_CAP, {"from": admin}
    )
    burn_mint_erc20.mint(alice, c.MINT_AMOUNT, {"from": admin})
    approve_tx = burn_mint_erc20.approve(
        topos_core_A, c.APPROVE_AMOUNT, {"from": alice}
    )
    assert approve_tx.events["Approval"].values() == [
        alice,
        topos_core_A.address,
        c.SEND_AMOUNT,
    ]
    # register the token onto ToposCore
    topos_core_A.deployToken(
        get_default_external_token_val(burn_mint_erc20.address),
        {"from": admin},
    )
    send_token_tx = topos_core_A.sendToken(
        c.TARGET_SUBNET_ID,
        bob,
        c.TOKEN_SYMBOL_X,
        c.SEND_AMOUNT,
        {"from": alice},
    )
    assert send_token_tx.events["Transfer"].values() == [
        alice,
        topos_core_A.address,
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


def test_send_token_reverts_on_burn_fail(admin, alice, bob, topos_core_A):
    topos_core_A.deployToken(get_default_internal_token_val(), {"from": admin})
    # should fail because alice does not have enough balance to burn
    with brownie.reverts():
        topos_core_A.sendToken(
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
    topos_core_A,
    BurnableMintableCappedERC20,
):
    tx = topos_core_A.deployToken(
        get_default_internal_token_val(), {"from": admin}
    )
    topos_core_A.giveToken(
        c.TOKEN_SYMBOL_X, alice, c.MINT_AMOUNT, {"from": admin}
    )
    burnable_mint_erc20 = BurnableMintableCappedERC20.at(
        tx.events["TokenDeployed"]["tokenAddress"]
    )
    approve_tx = burnable_mint_erc20.approve(
        topos_core_A, c.APPROVE_AMOUNT, {"from": alice}
    )
    assert approve_tx.events["Approval"].values() == [
        alice,
        topos_core_A.address,
        c.SEND_AMOUNT,
    ]
    send_token_tx = topos_core_A.sendToken(
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


def test_call_contract_emits_event(accounts, alice, topos_core_A):
    target_contract_addr = accounts.add()
    tx = topos_core_A.callContract(
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
    topos_core_A,
    BurnableMintableCappedERC20,
):
    tx = topos_core_A.deployToken(
        get_default_internal_token_val(), {"from": admin}
    )
    topos_core_A.giveToken(
        c.TOKEN_SYMBOL_X, alice, c.MINT_AMOUNT, {"from": admin}
    )
    burnable_mint_erc20 = BurnableMintableCappedERC20.at(
        tx.events["TokenDeployed"]["tokenAddress"]
    )
    burnable_mint_erc20.approve(
        topos_core_A, c.APPROVE_AMOUNT, {"from": alice}
    )
    target_contract_addr = accounts.add()
    tx = topos_core_A.callContractWithToken(
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
    admin, topos_core_A
):
    fixture_subnet_id = c.SOURCE_SUBNET_ID
    # should fail since the certificate is not present
    with brownie.reverts():
        topos_core_A.verifyContractCallData(
            c.CERT_ID, fixture_subnet_id, {"from": admin}
        )


def test_verify_contract_call_data_reverts_on_unidentified_subnet_id(
    admin, topos_core_A
):
    fixture_subnet_id = c.TARGET_SUBNET_ID
    push_dummy_cert(admin, topos_core_A)
    # should revert since fixture is set to source_subnet_id
    with brownie.reverts():
        topos_core_A.verifyContractCallData(
            c.CERT_ID, fixture_subnet_id, {"from": admin}
        )


def test_verify_contract_call_returns_true(admin, topos_core_A):
    fixture_subnet_id = c.SOURCE_SUBNET_ID
    push_dummy_cert(admin, topos_core_A)
    tx = topos_core_A.verifyContractCallData(
        c.CERT_ID, fixture_subnet_id, {"from": admin}
    )
    assert tx is True


def test_upgrade_emits_event(
    admin, topos_core_A, CodeHash, TokenDeployer, ToposCore
):
    admin_values = [[admin.address], 1]
    encoded_admin_params = encode(c.ADMIN_PARAMS, admin_values)
    topos_core_impl = deploy_new_tcc(admin, TokenDeployer, ToposCore)
    # verify that the current delegate is not the same as the new delegate
    assert (
        topos_core_A.implementation({"from": admin}) != topos_core_impl.address
    )
    code_hash = CodeHash.deploy({"from": admin})
    codehash = code_hash.getCodeHash(topos_core_impl.address)
    tx = topos_core_A.upgrade(
        topos_core_impl.address,
        codehash,
        encoded_admin_params,
        {"from": admin},
    )
    # the proxy storage should point to the new delegate address
    assert tx.events["Upgraded"]["implementation"] == topos_core_impl.address


# internal functions #
def push_dummy_cert(admin, topos_core_A):
    return topos_core_A.pushCertificate(
        encode(
            c.CERT_PARAMS,
            [
                c.CERT_ID,
                c.SOURCE_SUBNET_ID,
                c.STATE_ROOT,
                c.TX_ROOT,
                [c.TARGET_SUBNET_ID],
                c.VERIFIER,
                c.CERT_ID,
                c.DUMMY_DATA,
                c.DUMMY_DATA,
            ],
        ),
        c.CERT_POSITION,
        {"from": admin},
    )


def push_cert(admin, topos_core_A, cert_id, source_subnet_id, position):
    return topos_core_A.pushCertificate(
        encode(
            c.CERT_PARAMS,
            [
                c.CERT_ID,
                source_subnet_id,
                c.STATE_ROOT,
                c.TX_ROOT,
                [c.TARGET_SUBNET_ID],
                c.VERIFIER,
                cert_id,
                c.DUMMY_DATA,
                c.DUMMY_DATA,
            ],
        ),
        position,
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
    return encode(c.TOKEN_PARAMS, token_values)


def get_secondary_internal_token_val():
    token_values = [
        c.TOKEN_NAME,
        c.TOKEN_SYMBOL_Y,
        c.MINT_CAP,
        brownie.ZERO_ADDRESS,  # address zero since not yet deployed
        c.DAILY_MINT_LIMIT,
    ]
    return encode(c.TOKEN_PARAMS, token_values)


def get_default_external_token_val(address):
    token_values = [
        c.TOKEN_NAME,
        c.TOKEN_SYMBOL_X,
        c.MINT_CAP,
        address,  # specify deployed token address
        c.DAILY_MINT_LIMIT,
    ]
    return encode(c.TOKEN_PARAMS, token_values)


def get_default_mint_val(bob):
    mint_token_args = [
        c.SOURCE_SUBNET_ID,
        bob.address,
        c.TOKEN_SYMBOL_X,
        c.SEND_AMOUNT,
    ]
    return encode(c.MINT_TOKEN_PARAMS, mint_token_args)


def deploy_new_tcc(admin, TokenDeployer, ToposCore):
    token_deployer = TokenDeployer.deploy({"from": admin})
    return ToposCore.deploy(
        token_deployer.address, c.SOURCE_SUBNET_ID, {"from": admin}
    )


def get_hash(input):
    k = keccak.new(digest_bits=256)
    k.update(input)
    return k.hexdigest()


def get_token_key_hash(symbol):
    key_prefix = brownie.convert.to_bytes(
        get_hash("token-key".encode("utf-8")), "bytes32"
    )
    encoded_key = encode_abi_packed(
        ["bytes32", "string"], [key_prefix, symbol]
    )
    return "0x" + get_hash(encoded_key)
