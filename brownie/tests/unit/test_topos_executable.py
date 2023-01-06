import brownie
from Crypto.Hash import keccak
import eth_abi

import const as c


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
        brownie.convert.datatypes.HexString(c.SOURCE_SUBNET_ID, "bytes32"),
        dummy_address,
        brownie.convert.datatypes.HexString(get_selector_hash(), "bytes32"),
        c.MINIMUM_CERT_POSITION,
    ]


def test_execute_reverts_on_unknown_cert_id(
    accounts, admin, topos_core_contract_B, topos_executable
):
    invalid_cert_id = brownie.convert.to_bytes("0xdead", "bytes")
    dummy_address = accounts.add()
    topos_core_contract_B.pushCertificate(
        get_encoded_cert_params(c.CERT_ID, c.CERT_POSITION), {"from": admin}
    )
    data = get_call_contract_data(dummy_address, c.TARGET_SUBNET_ID)
    # should revert since the cert is not present
    with brownie.reverts():
        topos_executable.execute(
            invalid_cert_id, data, c.DUMMY_DATA, {"from": admin}
        )


def test_execute_reverts_on_false_target_subnet_id(
    accounts, admin, topos_core_contract_B, topos_executable
):
    invalid_target_subnet_id = brownie.convert.to_bytes("0x03", "bytes32")
    dummy_address = accounts.add()
    topos_core_contract_B.pushCertificate(
        get_encoded_cert_params(c.CERT_ID, c.CERT_POSITION), {"from": admin}
    )
    data = get_call_contract_data(dummy_address, invalid_target_subnet_id)
    # should revert since target subnet id is incorrect
    with brownie.reverts():
        topos_executable.execute(
            c.CERT_ID, data, c.DUMMY_DATA, {"from": admin}
        )


def test_execute_reverts_on_contract_call_already_executed(
    accounts, admin, topos_core_contract_B, topos_executable
):
    dummy_address = accounts.add()
    authorize_origin(dummy_address, admin, topos_executable)
    topos_core_contract_B.pushCertificate(
        get_encoded_cert_params(c.CERT_ID, c.CERT_POSITION), {"from": admin}
    )
    data = get_call_contract_data(dummy_address, c.TARGET_SUBNET_ID)
    topos_executable.execute(c.CERT_ID, data, c.DUMMY_DATA, {"from": admin})
    # should revert when executing the same call
    with brownie.reverts():
        topos_executable.execute(
            c.CERT_ID, data, c.DUMMY_DATA, {"from": admin}
        )


def test_execute_reverts_on_cert_position_lower_than_min_position(
    accounts, admin, topos_core_contract_B, topos_executable
):
    dummy_address = accounts.add()
    cert_position = 3
    authorize_origin(dummy_address, admin, topos_executable)
    topos_core_contract_B.pushCertificate(
        get_encoded_cert_params(c.CERT_ID, cert_position), {"from": admin}
    )
    data = get_call_contract_data(dummy_address, c.TARGET_SUBNET_ID)
    # should revert since the cert position < min cert position
    with brownie.reverts():
        topos_executable.execute(
            c.CERT_ID, data, c.DUMMY_DATA, {"from": admin}
        )


def test_execute_with_token_reverts_on_unknown_cert_id(
    accounts, admin, topos_core_contract_B, topos_executable
):
    invalid_cert_id = brownie.convert.to_bytes("0xdead", "bytes")
    dummy_address = accounts.add()
    topos_core_contract_B.pushCertificate(
        get_encoded_cert_params(c.CERT_ID, c.CERT_POSITION), {"from": admin}
    )
    data = get_call_contract_with_token_data(dummy_address, c.TARGET_SUBNET_ID)
    # should revert since the cert is not present
    with brownie.reverts():
        topos_executable.executeWithToken(
            invalid_cert_id, data, c.DUMMY_DATA, {"from": admin}
        )


def test_execute_with_token_reverts_on_false_target_subnet_id(
    accounts, admin, topos_core_contract_B, topos_executable
):
    invalid_target_subnet_id = brownie.convert.to_bytes("0x03", "bytes32")
    dummy_address = accounts.add()
    topos_core_contract_B.pushCertificate(
        get_encoded_cert_params(c.CERT_ID, c.CERT_POSITION), {"from": admin}
    )
    data = get_call_contract_with_token_data(
        dummy_address, invalid_target_subnet_id
    )
    # should revert since target subnet id is incorrect
    with brownie.reverts():
        topos_executable.executeWithToken(
            c.CERT_ID, data, c.DUMMY_DATA, {"from": admin}
        )


def test_execute_with_token_reverts_on_contract_call_already_executed(
    accounts, admin, topos_core_contract_B, topos_executable
):
    dummy_address = accounts.add()
    authorize_origin(dummy_address, admin, topos_executable)
    topos_core_contract_B.pushCertificate(
        get_encoded_cert_params(c.CERT_ID, c.CERT_POSITION), {"from": admin}
    )
    data = get_call_contract_with_token_data(dummy_address, c.TARGET_SUBNET_ID)
    topos_executable.executeWithToken(
        c.CERT_ID, data, c.DUMMY_DATA, {"from": admin}
    )
    # should revert when executing the same call
    with brownie.reverts():
        topos_executable.executeWithToken(
            c.CERT_ID, data, c.DUMMY_DATA, {"from": admin}
        )


def test_execute_with_token_reverts_on_cert_position_lower_than_min_position(
    accounts, admin, topos_core_contract_B, topos_executable
):
    dummy_address = accounts.add()
    cert_position = 3
    authorize_origin(dummy_address, admin, topos_executable)
    topos_core_contract_B.pushCertificate(
        get_encoded_cert_params(c.CERT_ID, cert_position), {"from": admin}
    )
    data = get_call_contract_with_token_data(dummy_address, c.TARGET_SUBNET_ID)
    # should revert since the cert position < min cert position
    with brownie.reverts():
        topos_executable.executeWithToken(
            c.CERT_ID, data, c.DUMMY_DATA, {"from": admin}
        )


# internal functions #
def authorize_origin(sender, spender, topos_executable):
    return topos_executable.authorizeOrigin(
        c.SOURCE_SUBNET_ID,
        sender,
        get_selector_hash(),
        c.MINIMUM_CERT_POSITION,
        {"from": spender},
    )


def get_call_contract_data(addr, subnet_id):
    return [
        c.DUMMY_DATA,  # tx_hash
        c.SOURCE_SUBNET_ID,
        addr,  # source_contract_addr
        subnet_id,
        addr,  # target_contract_addr
        get_payload_hash(),
        c.PAYLOAD,
        get_selector_hash(),
    ]


def get_call_contract_with_token_data(addr, subnet_id):
    return [
        c.DUMMY_DATA,  # tx_hash
        c.SOURCE_SUBNET_ID,
        addr,  # source_contract_addr
        subnet_id,
        addr,  # target_contract_addr
        get_payload_hash(),
        c.PAYLOAD,
        c.TOKEN_SYMBOL_X,
        c.SEND_AMOUNT,
        get_selector_hash(),
    ]


def get_encoded_cert_params(cert_id, cert_position):
    return eth_abi.encode(["bytes32", "uint256"], [cert_id, cert_position])


def get_payload_hash():
    k = keccak.new(digest_bits=256)
    k.update(c.PAYLOAD)
    return "0x" + k.hexdigest()


def get_selector_hash():
    k = keccak.new(digest_bits=256)
    k.update(c.DUMMY_DATA)
    return "0x" + k.hexdigest()
