import brownie
from Crypto.Hash import keccak
import eth_abi

# const
cert_bytes = "0xdeaf"
cert_height = 10
cert_id = brownie.convert.to_bytes(cert_bytes, "bytes")
daily_mint_limit = 100
decimals = 18
destination_subnet_id = brownie.convert.to_bytes("0x02", "bytes32")
dummy_data = brownie.convert.to_bytes("0x00", "bytes")
minimum_cert_height = 5
mint_cap = 1000
origin_subnet_id = brownie.convert.to_bytes("0x01", "bytes32")
send_amount = 10
token_name = "TokenX"
token_symbol = "TKX"

# payload
payload = brownie.convert.to_bytes("0xdead", "bytes")
k = keccak.new(digest_bits=256)
k.update(payload)
payload_hash = "0x" + k.hexdigest()

# function selector
selector = "changeValue"
k = keccak.new(digest_bits=256)
k.update(dummy_data)
selector_hash = "0x" + k.hexdigest()


def test_authorize_origin_reverts_on_unknown_admin(
    accounts, alice, topos_contracts
):
    dummy_address = accounts.add()
    topos_executable = topos_contracts[1]
    # should revert since alice is not an admin
    with brownie.reverts():
        topos_executable.authorizeOrigin(
            origin_subnet_id,
            dummy_address,
            selector_hash,
            minimum_cert_height,
            {"from": alice},
        )


def test_authorize_origin_emits_event(accounts, admin, topos_contracts):
    dummy_address = accounts.add()
    topos_executable = topos_contracts[1]
    tx = topos_executable.authorizeOrigin(
        origin_subnet_id,
        dummy_address,
        selector_hash,
        minimum_cert_height,
        {"from": admin},
    )
    assert tx.events["OriginAuthorized"].values() == [
        brownie.convert.datatypes.HexString(origin_subnet_id, "bytes32"),
        dummy_address,
        brownie.convert.datatypes.HexString(selector_hash, "bytes32"),
        minimum_cert_height,
    ]


def test_execute_reverts_on_unverified_cert_id(
    accounts, admin, topos_contracts
):
    invalid_cert_id = brownie.convert.to_bytes("0xdead", "bytes")
    dummy_address = accounts.add()
    encoded_cert_params = eth_abi.encode_abi(
        ["bytes", "uint256"], [cert_id, cert_height]
    )
    topos_core_contract = topos_contracts[0]
    topos_core_contract.verifyCertificate(encoded_cert_params, {"from": admin})

    contract_call_data = [
        dummy_data,  # tx_hash
        origin_subnet_id,
        dummy_address.address,  # origin_address
        destination_subnet_id,
        dummy_address.address,  # destination_contract_address
        payload_hash,
        payload,
        selector_hash,
    ]
    topos_executable = topos_contracts[1]
    # should revert since the cert is unverified
    with brownie.reverts():
        topos_executable.execute(
            invalid_cert_id, contract_call_data, dummy_data, {"from": admin}
        )


def test_execute_reverts_on_false_destination_id(
    accounts, admin, topos_contracts
):
    invalid_destination_subnet_id = brownie.convert.to_bytes("0x03", "bytes32")
    dummy_address = accounts.add()
    encoded_cert_params = eth_abi.encode_abi(
        ["bytes", "uint256"], [cert_id, cert_height]
    )
    topos_core_contract = topos_contracts[0]
    topos_core_contract.verifyCertificate(encoded_cert_params, {"from": admin})

    contract_call_data = [
        dummy_data,  # tx_hash
        origin_subnet_id,
        dummy_address.address,  # origin_address
        invalid_destination_subnet_id,
        dummy_address.address,  # destination_contract_address
        payload_hash,
        payload,
        selector_hash,
    ]
    topos_executable = topos_contracts[1]
    # should revert since the transaction is not meant for the receipient
    # destination subnet
    with brownie.reverts():
        topos_executable.execute(
            cert_id, contract_call_data, dummy_data, {"from": admin}
        )


def test_execute_reverts_on_contract_call_already_executed(
    accounts, admin, topos_contracts
):
    dummy_address = accounts.add()
    topos_executable = topos_contracts[1]
    topos_executable.authorizeOrigin(
        origin_subnet_id,
        dummy_address,
        selector_hash,
        minimum_cert_height,
        {"from": admin},
    )

    encoded_cert_params = eth_abi.encode_abi(
        ["bytes", "uint256"], [cert_id, cert_height]
    )
    topos_core_contract = topos_contracts[0]
    topos_core_contract.verifyCertificate(encoded_cert_params, {"from": admin})

    contract_call_data = [
        dummy_data,  # tx_hash
        origin_subnet_id,
        dummy_address.address,  # origin_address
        destination_subnet_id,
        dummy_address.address,  # destination_contract_address
        payload_hash,
        payload,
        selector_hash,
    ]
    topos_executable = topos_contracts[1]
    topos_executable.execute(
        cert_id, contract_call_data, dummy_data, {"from": admin}
    )
    # should revert when executing the same call
    with brownie.reverts():
        topos_executable.execute(
            cert_id, contract_call_data, dummy_data, {"from": admin}
        )


def test_execute_reverts_on_cert_height_lower_than_min_height(
    accounts, admin, topos_contracts
):
    dummy_address = accounts.add()
    cert_height = 4
    topos_executable = topos_contracts[1]
    topos_executable.authorizeOrigin(
        origin_subnet_id,
        dummy_address,
        selector_hash,
        minimum_cert_height,
        {"from": admin},
    )

    encoded_cert_params = eth_abi.encode_abi(
        ["bytes", "uint256"], [cert_id, cert_height]
    )
    topos_core_contract = topos_contracts[0]
    topos_core_contract.verifyCertificate(encoded_cert_params, {"from": admin})

    contract_call_data = [
        dummy_data,  # tx_hash
        origin_subnet_id,
        dummy_address.address,  # origin_address
        destination_subnet_id,
        dummy_address.address,  # destination_contract_address
        payload_hash,
        payload,
        selector_hash,
    ]
    topos_executable = topos_contracts[1]
    # should revert since the certificate height is less than the
    # minimum certificate height
    with brownie.reverts():
        topos_executable.execute(
            cert_id, contract_call_data, dummy_data, {"from": admin}
        )


def test_execute_with_token_reverts_on_unverified_cert_id(
    accounts, admin, topos_contracts
):
    invalid_cert_id = brownie.convert.to_bytes("0xdead", "bytes")
    dummy_address = accounts.add()
    encoded_cert_params = eth_abi.encode_abi(
        ["bytes", "uint256"], [cert_id, cert_height]
    )
    topos_core_contract = topos_contracts[0]
    topos_core_contract.verifyCertificate(encoded_cert_params, {"from": admin})

    contract_call_data = [
        dummy_data,  # tx_hash
        origin_subnet_id,
        dummy_address.address,  # origin_address
        destination_subnet_id,
        dummy_address.address,  # destination_contract_address
        payload_hash,
        payload,
        token_symbol,
        send_amount,
        selector_hash,
    ]
    topos_executable = topos_contracts[1]
    # should revert since the cert is unverified
    with brownie.reverts():
        topos_executable.executeWithToken(
            invalid_cert_id, contract_call_data, dummy_data, {"from": admin}
        )


def test_execute_with_token_reverts_on_false_destination_id(
    accounts, admin, topos_contracts
):
    invalid_destination_subnet_id = brownie.convert.to_bytes("0x03", "bytes32")
    dummy_address = accounts.add()
    encoded_cert_params = eth_abi.encode_abi(
        ["bytes", "uint256"], [cert_id, cert_height]
    )
    topos_core_contract = topos_contracts[0]
    topos_core_contract.verifyCertificate(encoded_cert_params, {"from": admin})

    contract_call_data = [
        dummy_data,  # tx_hash
        origin_subnet_id,
        dummy_address.address,  # origin_address
        invalid_destination_subnet_id,
        dummy_address.address,  # destination_contract_address
        payload_hash,
        payload,
        token_symbol,
        send_amount,
        selector_hash,
    ]
    topos_executable = topos_contracts[1]
    # should revert since the transaction is not meant for the receipient
    # destination subnet
    with brownie.reverts():
        topos_executable.executeWithToken(
            cert_id, contract_call_data, dummy_data, {"from": admin}
        )


def test_execute_with_token_reverts_on_contract_call_already_executed(
    accounts, admin, topos_contracts
):
    dummy_address = accounts.add()
    topos_executable = topos_contracts[1]
    topos_executable.authorizeOrigin(
        origin_subnet_id,
        dummy_address,
        selector_hash,
        minimum_cert_height,
        {"from": admin},
    )

    encoded_cert_params = eth_abi.encode_abi(
        ["bytes", "uint256"], [cert_id, cert_height]
    )
    topos_core_contract = topos_contracts[0]
    topos_core_contract.verifyCertificate(encoded_cert_params, {"from": admin})

    contract_call_data = [
        dummy_data,  # tx_hash
        origin_subnet_id,
        dummy_address.address,  # origin_address
        destination_subnet_id,
        dummy_address.address,  # destination_contract_address
        payload_hash,
        payload,
        token_symbol,
        send_amount,
        selector_hash,
    ]
    topos_executable = topos_contracts[1]
    topos_executable.executeWithToken(
        cert_id, contract_call_data, dummy_data, {"from": admin}
    )
    # should revert when executing the same call
    with brownie.reverts():
        topos_executable.executeWithToken(
            cert_id, contract_call_data, dummy_data, {"from": admin}
        )


def test_execute_with_token_reverts_on_cert_height_lower_than_min_height(
    accounts, admin, topos_contracts
):
    dummy_address = accounts.add()
    cert_height = 4
    topos_executable = topos_contracts[1]
    topos_executable.authorizeOrigin(
        origin_subnet_id,
        dummy_address,
        selector_hash,
        minimum_cert_height,
        {"from": admin},
    )

    encoded_cert_params = eth_abi.encode_abi(
        ["bytes", "uint256"], [cert_id, cert_height]
    )
    topos_core_contract = topos_contracts[0]
    topos_core_contract.verifyCertificate(encoded_cert_params, {"from": admin})

    contract_call_data = [
        dummy_data,  # tx_hash
        origin_subnet_id,
        dummy_address.address,  # origin_address
        destination_subnet_id,
        dummy_address.address,  # destination_contract_address
        payload_hash,
        payload,
        token_symbol,
        send_amount,
        selector_hash,
    ]
    topos_executable = topos_contracts[1]
    # should revert since the certificate height is less than the
    # minimum certificate height
    with brownie.reverts():
        topos_executable.executeWithToken(
            cert_id, contract_call_data, dummy_data, {"from": admin}
        )
