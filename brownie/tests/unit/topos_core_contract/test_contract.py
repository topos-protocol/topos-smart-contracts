import brownie
from Crypto.Hash import keccak
import eth_abi

# const
admin_threshold = 2
approve_amount = 10
cert_bytes = "0xdeaf"
cert_height = 5
cert_id = brownie.convert.to_bytes(cert_bytes, "bytes")
daily_mint_limit = 100
decimals = 18
destination_subnet_id = brownie.convert.to_bytes("0x02", "bytes32")
dummy_data = brownie.convert.to_bytes("0x00", "bytes")
mint_amount = 10
mint_cap = 1000
origin_subnet_id = brownie.convert.to_bytes("0x01", "bytes32")
send_amount = 10
token_name = "TokenX"
token_symbol = "TKX"
token_symbol_second = "TKY"

# token to be deployed args
token_params = [
    "string",
    "string",
    "uint8",
    "uint256",
    "address",
    "uint256",
]
token_values = [
    token_name,
    token_symbol,
    decimals,
    mint_cap,
    brownie.ZERO_ADDRESS,
    daily_mint_limit,
]
encoded_token_params = eth_abi.encode(token_params, token_values)


def test_verify_certificate_reverts_on_already_verified_certificate(
    admin, topos_core_contract
):
    encoded_cert_params = eth_abi.encode_abi(
        ["bytes", "uint256"], [cert_id, cert_height]
    )
    topos_core_contract.verifyCertificate(encoded_cert_params, {"from": admin})
    with brownie.reverts():
        # retry verifying the same cert
        topos_core_contract.verifyCertificate(
            encoded_cert_params, {"from": admin}
        )


def test_verify_certificate_emits_event(admin, topos_core_contract):
    encoded_cert_params = eth_abi.encode_abi(
        ["bytes", "uint256"], [cert_id, cert_height]
    )
    tx = topos_core_contract.verifyCertificate(
        encoded_cert_params, {"from": admin}
    )
    assert tx.events["CertVerified"].values() == [cert_bytes]


def test_set_token_daily_mint_limits_reverts_on_mismatch_symbol_length(
    admin, topos_core_contract
):
    # symbol and limit array lenghts should be 1:1 ratio
    symbols = [token_symbol, token_symbol_second]
    mint_limits = [mint_amount]
    with brownie.reverts():
        topos_core_contract.setTokenDailyMintLimits(
            symbols, mint_limits, {"from": admin}
        )


def test_set_token_daily_mint_limits_reverts_on_token_does_not_exist(
    admin, topos_core_contract
):
    symbols = [token_symbol]
    mint_limits = [mint_amount]
    # should fail because token not deployed yet
    with brownie.reverts():
        topos_core_contract.setTokenDailyMintLimits(
            symbols, mint_limits, {"from": admin}
        )


def test_set_token_daily_mint_limits_emits_event(admin, topos_core_contract):
    symbols = [token_symbol]
    mint_limits = [mint_amount]

    topos_core_contract.deployToken(encoded_token_params, {"from": admin})
    tx = topos_core_contract.setTokenDailyMintLimits(
        symbols, mint_limits, {"from": admin}
    )
    assert tx.events["TokenDailyMintLimitUpdated"].values() == [
        token_symbol,
        mint_amount,
    ]


def test_set_token_daily_mint_limits_allow_zero_limit(
    admin, alice, bob, topos_core_contract
):
    # token to be deployed args
    token_params = [
        "string",
        "string",
        "uint8",
        "uint256",
        "address",
        "uint256",
    ]
    token_values = [
        token_name,
        token_symbol,
        decimals,
        mint_cap,
        brownie.ZERO_ADDRESS,
        0,  # 0 daily mint limit = unlimited mint limit
    ]
    encoded_token_params = eth_abi.encode(token_params, token_values)
    topos_core_contract.deployToken(encoded_token_params, {"from": admin})
    verify_dummy_cert(admin, topos_core_contract)
    # execute asset transfer args
    mint_token_params = [
        "bytes",
        "address",
        "bytes32",
        "bytes32",
        "address",
        "string",
        "uint256",
    ]
    mint_token_values = [
        dummy_data,
        alice.address,
        origin_subnet_id,
        origin_subnet_id,
        bob.address,
        token_symbol,
        send_amount,
    ]
    encoded_mint_token_params = eth_abi.encode(
        mint_token_params, mint_token_values
    )
    tx = topos_core_contract.executeAssetTransfer(
        cert_id, encoded_mint_token_params, dummy_data, {"from": admin}
    )
    # the transaction should go through even without a daily mint limit set
    assert tx.events["Transfer"].values() == [
        brownie.ZERO_ADDRESS,
        bob.address,
        send_amount,
    ]


def test_deploy_token_reverts_on_token_already_deployed(
    admin, topos_core_contract
):
    topos_core_contract.deployToken(encoded_token_params, {"from": admin})
    # retry deploying the same token
    with brownie.reverts():
        topos_core_contract.deployToken(encoded_token_params, {"from": admin})


def test_deploy_token_external_token_emits_events(
    admin, topos_core_contract, BurnableMintableCappedERC20
):
    # deploy an external erc20 token
    burn_mint_erc20 = BurnableMintableCappedERC20.deploy(
        token_name, token_symbol, decimals, mint_cap, {"from": admin}
    )
    # token to be deployed args
    token_params = [
        "string",
        "string",
        "uint8",
        "uint256",
        "address",
        "uint256",
    ]
    token_values = [
        token_name,
        token_symbol,
        decimals,
        mint_cap,
        burn_mint_erc20.address,
        daily_mint_limit,
    ]
    encoded_token_params = eth_abi.encode(token_params, token_values)
    tx = topos_core_contract.deployToken(encoded_token_params, {"from": admin})
    assert tx.events["TokenDeployed"].values() == [
        token_symbol,
        burn_mint_erc20.address,
    ]


def test_deploy_token_emits_events(admin, topos_core_contract):
    tx = topos_core_contract.deployToken(encoded_token_params, {"from": admin})
    token_address = tx.events["TokenDeployed"]["tokenAddresses"]
    assert tx.events["TokenDailyMintLimitUpdated"].values() == [
        token_symbol,
        daily_mint_limit,
    ]
    assert tx.events["TokenDeployed"].values() == [token_symbol, token_address]


def test_setup_reverts_on_mismatch_admin_threshold(admin, topos_core_contract):
    # admin args
    new_admin_params = [
        "address[]",
        "uint256",
    ]
    new_admin_values = [[admin.address], 2]
    encoded_admin_params = eth_abi.encode(new_admin_params, new_admin_values)
    # should revert since one admin address was provided but
    # the threshold was set to 2
    with brownie.reverts():
        topos_core_contract.setup(encoded_admin_params, {"from": admin})


def test_setup_reverts_on_admin_threshold_cannot_be_zero(
    admin, topos_core_contract
):
    # admin args
    new_admin_params = [
        "address[]",
        "uint256",
    ]
    new_admin_values = [[admin.address], 0]
    encoded_admin_params = eth_abi.encode(new_admin_params, new_admin_values)
    # should revert since the threshold can't be zero
    with brownie.reverts():
        topos_core_contract.setup(encoded_admin_params, {"from": admin})


def test_setup_reverts_on_duplicate_admin(admin, topos_core_contract):
    # admin args
    new_admin_params = [
        "address[]",
        "uint256",
    ]
    new_admin_values = [[admin.address, admin.address], 2]
    encoded_admin_params = eth_abi.encode(new_admin_params, new_admin_values)
    # should revert since you can't have two admins with the same
    # address
    with brownie.reverts():
        topos_core_contract.setup(encoded_admin_params, {"from": admin})


def test_setup_reverts_on_zero_address_admin(admin, topos_core_contract):
    # admin args
    new_admin_params = [
        "address[]",
        "uint256",
    ]
    new_admin_values = [[brownie.ZERO_ADDRESS], 1]
    encoded_admin_params = eth_abi.encode(new_admin_params, new_admin_values)
    # should revert since the admin address can't be zero address
    with brownie.reverts():
        topos_core_contract.setup(encoded_admin_params, {"from": admin})


def test_execute_transfer_reverts_on_unverified_cert(
    admin, alice, bob, topos_core_contract
):
    # execute asset transfer args
    mint_token_params = [
        "bytes",
        "address",
        "bytes32",
        "bytes32",
        "address",
        "string",
        "uint256",
    ]
    mint_token_values = [
        dummy_data,
        alice.address,
        origin_subnet_id,
        destination_subnet_id,
        bob.address,
        token_symbol,
        send_amount,
    ]
    encoded_mint_token_params = eth_abi.encode(
        mint_token_params, mint_token_values
    )
    # should revert since the certificate wasn't verified
    with brownie.reverts():
        topos_core_contract.executeAssetTransfer(
            cert_id, encoded_mint_token_params, dummy_data, {"from": admin}
        )


def test_execute_transfer_reverts_on_invalid_subnet_id(
    admin, alice, bob, topos_core_contract
):
    # default destination cert id is set to "0x01"
    dummy_destination_subnet_id = brownie.convert.to_bytes("0x02", "bytes32")
    verify_dummy_cert(admin, topos_core_contract)

    # execute asset transfer args
    mint_token_params = [
        "bytes",
        "address",
        "bytes32",
        "bytes32",
        "address",
        "string",
        "uint256",
    ]
    mint_token_values = [
        dummy_data,
        alice.address,
        origin_subnet_id,
        dummy_destination_subnet_id,
        bob.address,
        token_symbol,
        send_amount,
    ]
    encoded_mint_token_params = eth_abi.encode(
        mint_token_params, mint_token_values
    )
    # should fail since the provided destination subnet id is different
    with brownie.reverts():
        topos_core_contract.executeAssetTransfer(
            cert_id, encoded_mint_token_params, dummy_data, {"from": admin}
        )


def test_execute_transfer_reverts_on_call_already_executed(
    admin, alice, bob, topos_core_contract
):
    topos_core_contract.deployToken(encoded_token_params, {"from": admin})
    verify_dummy_cert(admin, topos_core_contract)

    # execute asset transfer args
    mint_token_params = [
        "bytes",
        "address",
        "bytes32",
        "bytes32",
        "address",
        "string",
        "uint256",
    ]
    mint_token_values = [
        dummy_data,
        alice.address,
        origin_subnet_id,
        origin_subnet_id,
        bob.address,
        token_symbol,
        send_amount,
    ]
    encoded_mint_token_params = eth_abi.encode(
        mint_token_params, mint_token_values
    )
    topos_core_contract.executeAssetTransfer(
        cert_id, encoded_mint_token_params, dummy_data, {"from": admin}
    )
    # resending the same call should fail
    with brownie.reverts():
        topos_core_contract.executeAssetTransfer(
            cert_id, encoded_mint_token_params, dummy_data, {"from": admin}
        )


def test_execute_transfer_reverts_on_token_does_not_exist(
    admin, alice, bob, topos_core_contract
):
    dummy_token_symbol = "DUMMY"
    topos_core_contract.deployToken(encoded_token_params, {"from": admin})
    verify_dummy_cert(admin, topos_core_contract)
    # execute asset transfer args
    mint_token_params = [
        "bytes",
        "address",
        "bytes32",
        "bytes32",
        "address",
        "string",
        "uint256",
    ]
    mint_token_values = [
        dummy_data,
        alice.address,
        origin_subnet_id,
        origin_subnet_id,
        bob.address,
        dummy_token_symbol,
        send_amount,
    ]
    encoded_mint_token_params = eth_abi.encode(
        mint_token_params, mint_token_values
    )
    # should fail since the dummy token wasn't deployed on ToposCoreContract
    with brownie.reverts():
        topos_core_contract.executeAssetTransfer(
            cert_id, encoded_mint_token_params, dummy_data, {"from": admin}
        )


def test_execute_transfer_reverts_on_exceeding_daily_mint_limit(
    admin, alice, bob, topos_core_contract
):
    send_amount = 110
    topos_core_contract.deployToken(encoded_token_params, {"from": admin})
    verify_dummy_cert(admin, topos_core_contract)

    # execute asset transfer args
    mint_token_params = [
        "bytes",
        "address",
        "bytes32",
        "bytes32",
        "address",
        "string",
        "uint256",
    ]
    mint_token_values = [
        dummy_data,
        alice.address,
        origin_subnet_id,
        origin_subnet_id,
        bob.address,
        token_symbol,
        send_amount,
    ]
    encoded_mint_token_params = eth_abi.encode(
        mint_token_params, mint_token_values
    )
    # should fail since the send_amount is greater than daily_mint_limit
    with brownie.reverts():
        topos_core_contract.executeAssetTransfer(
            cert_id, encoded_mint_token_params, dummy_data, {"from": admin}
        )


def test_execute_transfer_reverts_on_external_cannot_mint_to_zero_address(
    admin,
    alice,
    topos_core_contract,
    BurnableMintableCappedERC20,
):
    # deploy an external erc20 token
    burn_mint_erc20 = BurnableMintableCappedERC20.deploy(
        token_name, token_symbol, decimals, mint_cap, {"from": admin}
    )

    # token to be deployed args
    token_params = [
        "string",
        "string",
        "uint8",
        "uint256",
        "address",
        "uint256",
    ]
    token_values = [
        token_name,
        token_symbol,
        decimals,
        mint_cap,
        burn_mint_erc20.address,
        daily_mint_limit,
    ]
    encoded_token_params = eth_abi.encode(token_params, token_values)
    # register the external token on ToposCoreContract
    topos_core_contract.deployToken(encoded_token_params, {"from": admin})

    # allocate some amount to the ToposCoreContract so it can mint/transfer
    # to the recipient
    burn_mint_erc20.mint(
        topos_core_contract.address, mint_amount, {"from": admin}
    )

    verify_dummy_cert(admin, topos_core_contract)

    # execute asset transfer args
    mint_token_params = [
        "bytes",
        "address",
        "bytes32",
        "bytes32",
        "address",
        "string",
        "uint256",
    ]
    mint_token_values = [
        dummy_data,
        alice.address,
        origin_subnet_id,
        origin_subnet_id,
        brownie.ZERO_ADDRESS,  # receiver
        token_symbol,
        send_amount,
    ]
    encoded_mint_token_params = eth_abi.encode(
        mint_token_params, mint_token_values
    )
    # should revert since the receiver address cannot be zero address
    with brownie.reverts():
        topos_core_contract.executeAssetTransfer(
            cert_id, encoded_mint_token_params, dummy_data, {"from": admin}
        )


def test_execute_transfer_external_token_transfer_emits_events(
    admin,
    alice,
    bob,
    topos_core_contract,
    BurnableMintableCappedERC20,
):
    # deploy an external erc20 token
    burn_mint_erc20 = BurnableMintableCappedERC20.deploy(
        token_name, token_symbol, decimals, mint_cap, {"from": admin}
    )

    # token to be deployed args
    token_params = [
        "string",
        "string",
        "uint8",
        "uint256",
        "address",
        "uint256",
    ]
    token_values = [
        token_name,
        token_symbol,
        decimals,
        mint_cap,
        burn_mint_erc20.address,
        daily_mint_limit,
    ]
    encoded_token_params = eth_abi.encode(token_params, token_values)
    # register the external token on ToposCoreContract
    topos_core_contract.deployToken(encoded_token_params, {"from": admin})

    # allocate some amount to the ToposCoreContract so it can mint/transfer
    # to the recipient
    burn_mint_erc20.mint(
        topos_core_contract.address, mint_amount, {"from": admin}
    )

    verify_dummy_cert(admin, topos_core_contract)

    # execute asset transfer args
    mint_token_params = [
        "bytes",
        "address",
        "bytes32",
        "bytes32",
        "address",
        "string",
        "uint256",
    ]
    mint_token_values = [
        dummy_data,
        alice.address,
        origin_subnet_id,
        origin_subnet_id,
        bob.address,
        token_symbol,
        send_amount,
    ]
    encoded_mint_token_params = eth_abi.encode(
        mint_token_params, mint_token_values
    )
    tx = topos_core_contract.executeAssetTransfer(
        cert_id, encoded_mint_token_params, dummy_data, {"from": admin}
    )
    assert tx.events["Transfer"].values() == [
        topos_core_contract.address,
        bob.address,
        send_amount,
    ]


def test_execute_transfer_emits_event(admin, alice, bob, topos_core_contract):
    topos_core_contract.deployToken(encoded_token_params, {"from": admin})
    verify_dummy_cert(admin, topos_core_contract)
    # execute asset transfer args
    mint_token_params = [
        "bytes",
        "address",
        "bytes32",
        "bytes32",
        "address",
        "string",
        "uint256",
    ]
    mint_token_values = [
        dummy_data,
        alice.address,
        origin_subnet_id,
        origin_subnet_id,
        bob.address,
        token_symbol,
        send_amount,
    ]
    encoded_mint_token_params = eth_abi.encode(
        mint_token_params, mint_token_values
    )
    tx = topos_core_contract.executeAssetTransfer(
        cert_id, encoded_mint_token_params, dummy_data, {"from": admin}
    )
    assert tx.events["Transfer"].values() == [
        brownie.ZERO_ADDRESS,
        bob.address,
        send_amount,
    ]


def test_send_token_reverts_on_token_does_not_exist(
    admin, alice, bob, topos_core_contract, BurnableMintableCappedERC20
):
    dummy_token_symbol = "DUMMY"
    tx = topos_core_contract.deployToken(encoded_token_params, {"from": admin})
    topos_core_contract.giveToken(
        token_symbol, alice, mint_amount, {"from": admin}
    )
    burnable_mint_erc20 = BurnableMintableCappedERC20.at(
        tx.events["TokenDeployed"]["tokenAddresses"]
    )
    burnable_mint_erc20.approve(
        topos_core_contract, approve_amount, {"from": alice}
    )
    # should revert since the dummy token wasn't deployed on ToposCoreContract
    with brownie.reverts():
        topos_core_contract.sendToken(
            destination_subnet_id,
            bob,
            dummy_token_symbol,
            send_amount,
            {"from": alice},
        )


def test_send_token_reverts_on_zero_amount(
    admin, alice, bob, topos_core_contract, BurnableMintableCappedERC20
):
    send_amount = 0
    tx = topos_core_contract.deployToken(encoded_token_params, {"from": admin})
    topos_core_contract.giveToken(
        token_symbol, alice, mint_amount, {"from": admin}
    )
    burnable_mint_erc20 = BurnableMintableCappedERC20.at(
        tx.events["TokenDeployed"]["tokenAddresses"]
    )
    burnable_mint_erc20.approve(
        topos_core_contract, approve_amount, {"from": alice}
    )
    # should revert since zero amount cannot be minted
    with brownie.reverts():
        topos_core_contract.sendToken(
            destination_subnet_id,
            bob,
            token_symbol,
            send_amount,
            {"from": alice},
        )


def test_send_token_reverts_on_external_token_burn_fail(
    admin, alice, bob, topos_core_contract, BurnableMintableCappedERC20
):
    # deploy an external erc20 token
    burn_mint_erc20 = BurnableMintableCappedERC20.deploy(
        token_name, token_symbol, decimals, mint_cap, {"from": admin}
    )

    # register the token onto ToposCoreContract
    token_params = [
        "string",
        "string",
        "uint8",
        "uint256",
        "address",
        "uint256",
    ]
    token_values = [
        token_name,
        token_symbol,
        decimals,
        mint_cap,
        burn_mint_erc20.address,
        daily_mint_limit,
    ]
    encoded_token_params = eth_abi.encode(token_params, token_values)
    topos_core_contract.deployToken(encoded_token_params, {"from": admin})

    # transaction should fail because alice does not have enough
    # balance to burn
    with brownie.reverts():
        topos_core_contract.sendToken(
            destination_subnet_id,
            bob,
            token_symbol,
            send_amount,
            {"from": alice},
        )


def test_send_token_external_token_emits_events(
    admin, alice, bob, topos_core_contract, BurnableMintableCappedERC20
):
    # deploy an external erc20 token
    burn_mint_erc20 = BurnableMintableCappedERC20.deploy(
        token_name, token_symbol, decimals, mint_cap, {"from": admin}
    )
    burn_mint_erc20.mint(alice, mint_amount, {"from": admin})
    approve_tx = burn_mint_erc20.approve(
        topos_core_contract, approve_amount, {"from": alice}
    )
    assert approve_tx.events["Approval"].values() == [
        alice,
        topos_core_contract.address,
        send_amount,
    ]

    # register the token onto ToposCoreContract
    token_params = [
        "string",
        "string",
        "uint8",
        "uint256",
        "address",
        "uint256",
    ]
    token_values = [
        token_name,
        token_symbol,
        decimals,
        mint_cap,
        burn_mint_erc20.address,
        daily_mint_limit,
    ]
    encoded_token_params = eth_abi.encode(token_params, token_values)
    topos_core_contract.deployToken(encoded_token_params, {"from": admin})

    send_token_tx = topos_core_contract.sendToken(
        destination_subnet_id, bob, token_symbol, send_amount, {"from": alice}
    )
    assert send_token_tx.events["Transfer"].values() == [
        alice,
        topos_core_contract.address,
        send_amount,
    ]
    assert send_token_tx.events["TokenSent"].values() == [
        alice.address,
        brownie.convert.datatypes.HexString(origin_subnet_id, "bytes32"),
        brownie.convert.datatypes.HexString(destination_subnet_id, "bytes32"),
        bob.address,
        token_symbol,
        send_amount,
    ]


def test_send_token_reverts_on_burn_fail(
    admin, alice, bob, topos_core_contract
):
    topos_core_contract.deployToken(encoded_token_params, {"from": admin})
    # transaction should fail because alice does not have enough
    # balance to burn
    with brownie.reverts():
        topos_core_contract.sendToken(
            destination_subnet_id,
            bob,
            token_symbol,
            send_amount,
            {"from": alice},
        )


def test_send_token_emits_events(
    admin, alice, bob, topos_core_contract, BurnableMintableCappedERC20
):
    tx = topos_core_contract.deployToken(encoded_token_params, {"from": admin})
    topos_core_contract.giveToken(
        token_symbol, alice, mint_amount, {"from": admin}
    )
    burnable_mint_erc20 = BurnableMintableCappedERC20.at(
        tx.events["TokenDeployed"]["tokenAddresses"]
    )
    approve_tx = burnable_mint_erc20.approve(
        topos_core_contract, approve_amount, {"from": alice}
    )
    assert approve_tx.events["Approval"].values() == [
        alice,
        topos_core_contract.address,
        send_amount,
    ]

    send_token_tx = topos_core_contract.sendToken(
        destination_subnet_id,
        bob,
        token_symbol,
        send_amount,
        {"from": alice},
    )
    assert send_token_tx.events["Transfer"].values() == [
        alice,
        brownie.ZERO_ADDRESS,
        send_amount,
    ]
    assert send_token_tx.events["TokenSent"].values() == [
        alice.address,
        brownie.convert.datatypes.HexString(origin_subnet_id, "bytes32"),
        brownie.convert.datatypes.HexString(destination_subnet_id, "bytes32"),
        bob.address,
        token_symbol,
        send_amount,
    ]


def test_call_contract_emits_event(accounts, alice, topos_core_contract):
    destination_contract_addr = accounts.add()
    tx = topos_core_contract.callContract(
        destination_subnet_id,
        destination_contract_addr,
        dummy_data,
        {"from": alice},
    )
    k = keccak.new(digest_bits=256)
    k.update(dummy_data)
    assert tx.events["ContractCall"].values() == [
        brownie.convert.datatypes.HexString(origin_subnet_id, "bytes32"),
        alice.address,
        brownie.convert.datatypes.HexString(destination_subnet_id, "bytes32"),
        destination_contract_addr.address,
        "0x" + k.hexdigest(),
        brownie.convert.datatypes.HexString(dummy_data, "bytes"),
    ]


def test_call_contract_with_token_emits_event(
    accounts, admin, alice, topos_core_contract, BurnableMintableCappedERC20
):
    tx = topos_core_contract.deployToken(encoded_token_params, {"from": admin})
    topos_core_contract.giveToken(
        token_symbol, alice, mint_amount, {"from": admin}
    )
    burnable_mint_erc20 = BurnableMintableCappedERC20.at(
        tx.events["TokenDeployed"]["tokenAddresses"]
    )
    burnable_mint_erc20.approve(
        topos_core_contract, approve_amount, {"from": alice}
    )
    destination_contract_addr = accounts.add()
    tx = topos_core_contract.callContractWithToken(
        destination_subnet_id,
        destination_contract_addr,
        dummy_data,
        token_symbol,
        send_amount,
        {"from": alice},
    )
    k = keccak.new(digest_bits=256)
    k.update(dummy_data)
    assert tx.events["ContractCallWithToken"].values() == [
        brownie.convert.datatypes.HexString(origin_subnet_id, "bytes32"),
        alice.address,
        brownie.convert.datatypes.HexString(destination_subnet_id, "bytes32"),
        destination_contract_addr.address,
        "0x" + k.hexdigest(),
        brownie.convert.datatypes.HexString(dummy_data, "bytes"),
        token_symbol,
        send_amount,
    ]


def test_verify_contract_call_data_reverts_on_cert_not_verified(
    admin, topos_core_contract
):
    fixture_subnet_id = origin_subnet_id
    # should fail since the certificate is nor verified yet
    with brownie.reverts():
        topos_core_contract.verifyContractCallData(
            cert_id, fixture_subnet_id, {"from": admin}
        )


def test_verify_contract_call_data_reverts_on_unidentified_subnet_id(
    admin, topos_core_contract
):
    fixture_subnet_id = destination_subnet_id
    cert_params = ["bytes", "uint256"]
    cert_values = [cert_id, cert_height]
    encoded_cert_params = eth_abi.encode(cert_params, cert_values)
    topos_core_contract.verifyCertificate(encoded_cert_params, {"from": admin})
    # should fail since the subnet ID entered in the constructor
    # is equal to source_subnet_id
    with brownie.reverts():
        topos_core_contract.verifyContractCallData(
            cert_id, fixture_subnet_id, {"from": admin}
        )


def test_verify_contract_call_returns_true(admin, topos_core_contract):
    fixture_subnet_id = origin_subnet_id
    cert_params = ["bytes", "uint256"]
    cert_values = [cert_id, cert_height]
    encoded_cert_params = eth_abi.encode(cert_params, cert_values)
    topos_core_contract.verifyCertificate(encoded_cert_params, {"from": admin})
    tx = topos_core_contract.verifyContractCallData(
        cert_id, fixture_subnet_id, {"from": admin}
    )
    assert tx == [True, cert_height]


# internal functions #
def verify_dummy_cert(admin, topos_core_contract):
    cert_params = ["bytes", "uint256"]
    cert_values = [cert_id, cert_height]
    encoded_cert_params = eth_abi.encode(cert_params, cert_values)
    topos_core_contract.verifyCertificate(encoded_cert_params, {"from": admin})
