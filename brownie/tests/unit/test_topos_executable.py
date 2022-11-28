import brownie
from Crypto.Hash import keccak
import eth_abi

# const
cert_bytes = "0xdeaf"
cert_height = 10
cert_id = brownie.convert.to_bytes(cert_bytes, "bytes")
destination_subnet_id = brownie.convert.to_bytes("0x02", "bytes32")
dummy_data = brownie.convert.to_bytes("0x00", "bytes")
encoded_cert_params = eth_abi.encode_abi(
    ["bytes", "uint256"], [cert_id, cert_height]
)
minimum_cert_height = 5
origin_subnet_id = brownie.convert.to_bytes("0x01", "bytes32")
send_amount = 10
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
    accounts, alice, topos_executable
):
    dummy_address = accounts.add()
    # should revert since alice is not an admin
    with brownie.reverts():
        authorize_origin(dummy_address, alice, topos_executable)


def test_authorize_origin_emits_event(accounts, admin, topos_executable):
    dummy_address = accounts.add()
    tx = authorize_origin(dummy_address, admin, topos_executable)
    assert tx.events["OriginAuthorized"].values() == [
        brownie.convert.datatypes.HexString(origin_subnet_id, "bytes32"),
        dummy_address,
        brownie.convert.datatypes.HexString(selector_hash, "bytes32"),
        minimum_cert_height,
    ]


def test_execute_reverts_on_unverified_cert_id(
    accounts, admin, topos_core_contract_B, topos_executable
):
    invalid_cert_id = brownie.convert.to_bytes("0xdead", "bytes")
    dummy_address = accounts.add()
    topos_core_contract_B.verifyCertificate(
        encoded_cert_params, {"from": admin}
    )
    data = get_call_contract_data(dummy_address, destination_subnet_id)
    # should revert since the cert is unverified
    with brownie.reverts():
        topos_executable.execute(
            invalid_cert_id, data, dummy_data, {"from": admin}
        )


def test_execute_reverts_on_false_destination_id(
    accounts, admin, topos_core_contract_B, topos_executable
):
    invalid_destination_subnet_id = brownie.convert.to_bytes("0x03", "bytes32")
    dummy_address = accounts.add()
    topos_core_contract_B.verifyCertificate(
        encoded_cert_params, {"from": admin}
    )
    data = get_call_contract_data(dummy_address, invalid_destination_subnet_id)
    # should revert since destination subnet id is incorrect
    with brownie.reverts():
        topos_executable.execute(cert_id, data, dummy_data, {"from": admin})


def test_execute_reverts_on_contract_call_already_executed(
    accounts, admin, topos_core_contract_B, topos_executable
):
    dummy_address = accounts.add()
    authorize_origin(dummy_address, admin, topos_executable)
    topos_core_contract_B.verifyCertificate(
        encoded_cert_params, {"from": admin}
    )
    data = get_call_contract_data(dummy_address, destination_subnet_id)
    topos_executable.execute(cert_id, data, dummy_data, {"from": admin})
    # should revert when executing the same call
    with brownie.reverts():
        topos_executable.execute(cert_id, data, dummy_data, {"from": admin})


def test_execute_reverts_on_cert_height_lower_than_min_height(
    accounts, admin, topos_core_contract_B, topos_executable
):
    dummy_address = accounts.add()
    cert_height = 4
    authorize_origin(dummy_address, admin, topos_executable)
    encoded_cert_params = eth_abi.encode_abi(
        ["bytes", "uint256"], [cert_id, cert_height]
    )
    topos_core_contract_B.verifyCertificate(
        encoded_cert_params, {"from": admin}
    )
    data = get_call_contract_data(dummy_address, destination_subnet_id)
    # should revert since the cert height < min cert height
    with brownie.reverts():
        topos_executable.execute(cert_id, data, dummy_data, {"from": admin})


def test_execute_with_token_reverts_on_unverified_cert_id(
    accounts, admin, topos_core_contract_B, topos_executable
):
    invalid_cert_id = brownie.convert.to_bytes("0xdead", "bytes")
    dummy_address = accounts.add()
    topos_core_contract_B.verifyCertificate(
        encoded_cert_params, {"from": admin}
    )
    data = get_call_contract_with_token_data(
        dummy_address, destination_subnet_id
    )
    # should revert since the cert is unverified
    with brownie.reverts():
        topos_executable.executeWithToken(
            invalid_cert_id, data, dummy_data, {"from": admin}
        )


def test_execute_with_token_reverts_on_false_destination_id(
    accounts, admin, topos_core_contract_B, topos_executable
):
    invalid_destination_subnet_id = brownie.convert.to_bytes("0x03", "bytes32")
    dummy_address = accounts.add()
    topos_core_contract_B.verifyCertificate(
        encoded_cert_params, {"from": admin}
    )
    data = get_call_contract_with_token_data(
        dummy_address, invalid_destination_subnet_id
    )
    # should revert since destination subnet id is incorrect
    with brownie.reverts():
        topos_executable.executeWithToken(
            cert_id, data, dummy_data, {"from": admin}
        )


def test_execute_with_token_reverts_on_contract_call_already_executed(
    accounts, admin, topos_core_contract_B, topos_executable
):
    dummy_address = accounts.add()
    authorize_origin(dummy_address, admin, topos_executable)
    topos_core_contract_B.verifyCertificate(
        encoded_cert_params, {"from": admin}
    )
    data = get_call_contract_with_token_data(
        dummy_address, destination_subnet_id
    )
    topos_executable.executeWithToken(
        cert_id, data, dummy_data, {"from": admin}
    )
    # should revert when executing the same call
    with brownie.reverts():
        topos_executable.executeWithToken(
            cert_id, data, dummy_data, {"from": admin}
        )


def test_execute_with_token_reverts_on_cert_height_lower_than_min_height(
    accounts, admin, topos_core_contract_B, topos_executable
):
    dummy_address = accounts.add()
    cert_height = 4
    authorize_origin(dummy_address, admin, topos_executable)
    encoded_cert_params = eth_abi.encode_abi(
        ["bytes", "uint256"], [cert_id, cert_height]
    )
    topos_core_contract_B.verifyCertificate(
        encoded_cert_params, {"from": admin}
    )
    data = get_call_contract_with_token_data(
        dummy_address, destination_subnet_id
    )
    # should revert since the cert height < min cert height
    with brownie.reverts():
        topos_executable.executeWithToken(
            cert_id, data, dummy_data, {"from": admin}
        )


# internal functions #
def authorize_origin(sender, spender, topos_executable):
    return topos_executable.authorizeOrigin(
        origin_subnet_id,
        sender,
        selector_hash,
        minimum_cert_height,
        {"from": spender},
    )


def get_call_contract_data(addr, subnet_id):
    return [
        dummy_data,  # tx_hash
        origin_subnet_id,
        addr,  # origin_address
        subnet_id,
        addr,  # destination_contract_address
        payload_hash,
        payload,
        selector_hash,
    ]


def get_call_contract_with_token_data(addr, subnet_id):
    return [
        dummy_data,  # tx_hash
        origin_subnet_id,
        addr,  # origin_address
        subnet_id,
        addr,  # destination_contract_address
        payload_hash,
        payload,
        token_symbol,
        send_amount,
        selector_hash,
    ]
