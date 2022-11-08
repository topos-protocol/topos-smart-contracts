import brownie
import eth_abi
from brownie import (
    CrossSubnetArbitraryCall,
    CrossSubnetArbitraryCallCreationCode,
    TokenDeployer,
    ToposCoreContract,
    ConstAddressDeployer,
    accounts,
    network,
)
import logging

LOGGER = logging.getLogger(__name__)

# constants
arbitrary_call_value = "This is a test message"
alice_private = (
    "0x99B3C12287537E38C90A9219D4CB074A89A16E9CDB20BF85728EBD97C343E342"
)
bob_private = (
    "0x8075991ce870b93a8870eca0c0f91913d12f47948ca0fd25b49c6fa7cdbeee8b"
)
subnet_A_id = brownie.convert.to_bytes("0x01", "bytes32")
subnet_B_id = brownie.convert.to_bytes("0x02", "bytes32")
command_id = brownie.convert.to_bytes("0x0001", "bytes32")
dummy_cert_id = brownie.convert.to_bytes("0xefaa", "bytes")


def test_cross_subnet_arbitrary_call():
    # Network A
    LOGGER.info("Switching to subnet network A")
    switch_network("A")
    deploy_initial_contracts(subnet_A_id)
    set_remote_value_tx = set_remote_value_on_sending_subnet()

    # Events fetched by the automation webservice
    # get transaction data from the events
    LOGGER.info(f"set_remote_value_tx.events: {set_remote_value_tx.events}")

    # Network B
    LOGGER.info("Switching to subnet network B")
    switch_network("B")
    deploy_initial_contracts(subnet_B_id)
    approve_and_execute_on_receiving_subnet(set_remote_value_tx)
    assert xs_arbitrary_call_B.value() == arbitrary_call_value


def deploy_initial_contracts(network_subnet_id):
    accounts.add(alice_private)
    accounts.add(bob_private)
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
        eth_abi.encode_abi(
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
        network.connect("substrate-subnet-network-A")
    if subnet_network == "B":
        network.connect("substrate-subnet-network-B")


def set_remote_value_on_sending_subnet():
    # send arbitrary command to subnetB
    return xs_arbitrary_call_A.setRemoteValue(
        subnet_B_id,
        xs_arbitrary_call_A.address,
        arbitrary_call_value,
        {"from": accounts[0]},
    )


def approve_and_execute_on_receiving_subnet(set_remote_value_tx):
    contract_call_event = set_remote_value_tx.events["ContractCall"]
    sender = contract_call_event["sender"]
    destination_subnet_id = contract_call_event["destinationSubnetId"]
    destination_contract_address = contract_call_event[
        "destinationContractAddress"
    ]
    payload_hash = contract_call_event["payloadHash"]
    payload = contract_call_event["payload"]

    approve_contract_call_params = [
        "bytes32",
        "address",
        "address",
        "bytes32",
        "bytes",
        "uint256",
    ]

    approve_contract_call_values = [
        destination_subnet_id,
        destination_contract_address,
        sender,
        payload_hash,
        brownie.convert.to_bytes(set_remote_value_tx.txid, "bytes32"),
        0,
    ]

    encoded_call = eth_abi.encode_abi(
        approve_contract_call_params, approve_contract_call_values
    )
    # approve the arbitrary contract call
    approve_contract_call_tx = topos_core_contract_B.approveContractCall(
        encoded_call,
        command_id,
        {"from": accounts[0]},
    )
    LOGGER.info(f"Approved Contract Call: {approve_contract_call_tx.events}")

    # finally execute the arbitrary call via the ToposExecutor `execute`
    xs_arbitrary_call_B.execute(
        dummy_cert_id,
        command_id,
        destination_subnet_id,
        destination_contract_address,
        payload,
        {"from": accounts[0]},
    )
