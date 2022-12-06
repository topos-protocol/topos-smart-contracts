import brownie
from Crypto.Hash import keccak
import eth_abi
import logging
import pytest

from brownie import (
    accounts,
    ConstAddressDeployer,
    CrossSubnetArbitraryCall,
    CrossSubnetArbitraryCallCreationCode,
    network,
    TokenDeployer,
    ToposCoreContract,
)

LOGGER = logging.getLogger(__name__)

# constants
arbitrary_call_value = "This is a test message"
dummy_cert_position = 11
dummy_cert_id = brownie.convert.to_bytes("0xdeaf", "bytes")
dummy_xs_proof = brownie.convert.to_bytes("0x0002", "bytes")
min_cert_position_admin = 10
subnet_A_id = brownie.convert.to_bytes("0x01", "bytes32")
subnet_B_id = brownie.convert.to_bytes("0x02", "bytes32")
selector_hash = keccak.new(
    digest_bits=256
)  # get keccak256 hash of the target function
selector_hash.update("changeValue".encode("utf-8"))
selector = selector_hash.hexdigest()
tx_hash = brownie.convert.to_bytes("0x01", "bytes")


@pytest.mark.skip_coverage
def test_cross_subnet_contract_call():
    # Network A
    LOGGER.info("Switching to subnet network A")
    switch_network("A")
    deploy_initial_contracts(subnet_A_id)
    set_remote_value_tx = set_remote_value_on_sending_subnet()

    # Events fetched by the automation webservice
    # get transaction data from the events
    LOGGER.info(f"set_remote_value_tx.events: {set_remote_value_tx.events}")
    fast_forward_nonce(3)

    # Network B
    LOGGER.info("Switching to subnet network B")
    switch_network("B")
    deploy_initial_contracts(subnet_B_id)
    # if you don't validate a cert then the mint function would fail
    validate_dummy_cert(topos_core_contract_B)
    approve_and_execute_on_receiving_subnet(set_remote_value_tx)
    assert xs_arbitrary_call_B.value() == arbitrary_call_value


def deploy_initial_contracts(network_subnet_id):
    # deploy constant address deployer
    const_address_deployer = ConstAddressDeployer.deploy({"from": accounts[0]})
    LOGGER.info(
        f"ConstantAddressDeployer address: {const_address_deployer.address}"
    )

    # deploy token deployer
    token_deployer_salt = brownie.convert.to_bytes("0xf7", "bytes32")
    const_address_deployer_tx = const_address_deployer.deploy(
        TokenDeployer.bytecode,
        token_deployer_salt,
        {"from": accounts[0]},
    )
    token_deployer_address = const_address_deployer_tx.events["Deployed"][
        "deployedAddress"
    ]
    LOGGER.info(f"TokenDeployer address: {token_deployer_address}")

    # deploy ToposCoreContract
    topos_core_contract = ToposCoreContract.deploy(
        token_deployer_address,
        network_subnet_id,
        {"from": accounts[0]},
    )
    LOGGER.info(f"ToposCoreContract address: {topos_core_contract.address}")

    # deploy the cross subnet arbitrary call creation code getter contract
    creation_code_getter = CrossSubnetArbitraryCallCreationCode.deploy(
        {"from": accounts[0]},
    )
    xs_arbitrary_call_creation_code = creation_code_getter.getCreationBytecode(
        topos_core_contract.address
    )

    # deploy the cross subnet arbitrary call contract
    xs_arbitrary_call_salt = brownie.convert.to_bytes("0xf8", "bytes32")
    xs_arbitrary_call_tx = const_address_deployer.deploy(
        xs_arbitrary_call_creation_code,
        xs_arbitrary_call_salt,
        {"from": accounts[0]},
    )
    xs_arbitrary_call_address = xs_arbitrary_call_tx.events["Deployed"][
        "deployedAddress"
    ]
    xs_arbitrary_call = CrossSubnetArbitraryCall.at(xs_arbitrary_call_address)
    LOGGER.info(
        f"CrossSubnetArbitraryCall address: {xs_arbitrary_call_address}"
    )

    # set admin for ToposCoreContract
    admin_threshold = 1
    topos_core_contract.setup(
        eth_abi.encode(
            ["address[]", "uint256"],
            [[accounts[0].address], admin_threshold],
        ),
        {"from": accounts[0]},
    )
    if network_subnet_id == subnet_A_id:
        global xs_arbitrary_call_A
        xs_arbitrary_call_A = xs_arbitrary_call
    if network_subnet_id == subnet_B_id:
        global topos_core_contract_B
        global xs_arbitrary_call_B
        topos_core_contract_B = topos_core_contract
        xs_arbitrary_call_B = xs_arbitrary_call


def switch_network(subnet_network):
    network.disconnect()
    if subnet_network == "A":
        network.connect("development")
    if subnet_network == "B":
        network.connect("development-two")


def validate_dummy_cert(topos_core_contract):
    cert_params = ["bytes", "uint256"]
    cert_values = [dummy_cert_id, dummy_cert_position]
    encoded_cert_params = eth_abi.encode(cert_params, cert_values)
    topos_core_contract.verifyCertificate(
        encoded_cert_params, {"from": accounts[0]}
    )


def set_remote_value_on_sending_subnet():
    # send arbitrary command to subnetB
    return xs_arbitrary_call_A.setRemoteValue(
        subnet_B_id,
        xs_arbitrary_call_A.address,
        arbitrary_call_value,
        {"from": accounts[0]},
    )


def approve_and_execute_on_receiving_subnet(
    set_remote_value_tx,
):
    # events as seen by the web-service
    contract_call_event = set_remote_value_tx.events["ContractCall"]
    source_subnet_id = contract_call_event["sourceSubnetId"]
    source_contract_addr = contract_call_event["sourceContractAddr"]
    target_subnet_id = contract_call_event["targetSubnetId"]
    destination_contract_address = contract_call_event[
        "destinationContractAddress"
    ]
    payload_hash = contract_call_event["payloadHash"]
    payload = contract_call_event["payload"]

    # set the admin manually
    xs_arbitrary_call_B.setAdmin({"from": accounts[0]})

    # authorize the origin
    xs_arbitrary_call_B.authorizeOrigin(
        source_subnet_id,
        source_contract_addr,
        selector,
        min_cert_position_admin,
        {"from": accounts[0]},
    )

    execute_values = [
        tx_hash,
        source_subnet_id,
        source_contract_addr,
        target_subnet_id,
        destination_contract_address,
        payload_hash,
        payload,
        selector,
    ]

    # finally execute the arbitrary call via the ToposExecutor `execute`
    xs_arbitrary_call_B.execute(
        dummy_cert_id,
        execute_values,
        dummy_xs_proof,
        {"from": accounts[0]},
    )


def fast_forward_nonce(times):
    for _ in range(times):
        accounts[0].transfer(accounts[1], "10 ether")
