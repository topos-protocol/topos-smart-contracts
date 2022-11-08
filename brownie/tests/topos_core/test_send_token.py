import brownie
import eth_abi
from brownie import (
    BurnableMintableCappedERC20,
    TokenDeployer,
    ToposCoreContract,
    ConstAddressDeployer,
    accounts,
    network,
)
import logging

LOGGER = logging.getLogger(__name__)

# Constants
alice_private = (
    "0x99B3C12287537E38C90A9219D4CB074A89A16E9CDB20BF85728EBD97C343E342"
)
bob_private = (
    "0x8075991ce870b93a8870eca0c0f91913d12f47948ca0fd25b49c6fa7cdbeee8b"
)
send_amount = 50
dummy_data = brownie.convert.to_bytes("0x00", "bytes")
subnet_A_id = brownie.convert.to_bytes("0x01", "bytes32")
subnet_B_id = brownie.convert.to_bytes("0x02", "bytes32")
token_symbol = "TKX"
mint_cap = 1000
daily_mint_limit = 100
mint_amount = 100
approve_amount = 50
send_amount = 50


def test_send_token():
    # Network A
    LOGGER.info("Switching to subnet network A")
    switch_network("A")
    deploy_initial_contracts(subnet_A_id)
    token_sent_event = send_token()

    # Event logs as seen by the automation web-service
    _ = token_sent_event["sender"]
    _ = token_sent_event["destinationSubnetId"]
    receiver = token_sent_event["receiver"]
    symbol = token_sent_event["symbol"]
    amount = token_sent_event["amount"]

    # Network B
    LOGGER.info("Switching to subnet network B")
    switch_network("B")
    deploy_initial_contracts(subnet_B_id)
    mint_token(topos_core_contract_B, symbol, receiver, amount)
    token_address = topos_core_contract_B.tokenAddresses(token_symbol)
    burnable_mint_erc20_B = BurnableMintableCappedERC20.at(token_address)
    assert burnable_mint_erc20_B.balanceOf(receiver) == send_amount


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

    # deploy a token
    token_params = [
        "string",
        "string",
        "uint8",
        "uint256",
        "address",
        "uint256",
    ]
    token_values = [
        "TokenX",
        token_symbol,
        18,
        mint_cap,
        brownie.ZERO_ADDRESS,
        daily_mint_limit,
    ]
    encoded_token_params = eth_abi.encode_abi(token_params, token_values)

    deploy_token_tx = topos_core_contract.deployToken(
        encoded_token_params, {"from": accounts[0]}
    )
    LOGGER.info(
        "TokenX address: "
        + f"{deploy_token_tx.events['TokenDeployed']['tokenAddresses']}"
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
        # mint some amount for the sender
        # we don't need to do this for pre-existing tokens, given that
        # the sender has some balance to transfer in his/her account
        mint_token(
            topos_core_contract, token_symbol, accounts[0].address, mint_amount
        )
        # get ERC20 contract at the deployed address
        burnable_mint_erc20 = BurnableMintableCappedERC20.at(
            deploy_token_tx.events["TokenDeployed"]["tokenAddresses"]
        )
        # approve toposCoreContract to spend on behalf of the sender
        burnable_mint_erc20.approve(
            topos_core_contract, approve_amount, {"from": accounts[0]}
        )
        global topos_core_contract_A
        topos_core_contract_A = topos_core_contract
    if network_subnet_id == subnet_B_id:
        global topos_core_contract_B
        topos_core_contract_B = topos_core_contract


def send_token():
    send_token_tx = topos_core_contract_A.sendToken(
        subnet_B_id,
        accounts[1],
        token_symbol,
        send_amount,
        {"from": accounts[0]},
    )
    token_sent_event = send_token_tx.events["TokenSent"]
    return token_sent_event


def mint_token(topos_core_contract, symbol, receiver, amount):
    mint_token_params = ["string", "address", "uint256"]
    mint_token_values = [
        symbol,
        receiver,
        amount,
    ]
    encoded_token_params = eth_abi.encode_abi(
        mint_token_params, mint_token_values
    )
    topos_core_contract.mintToken(
        dummy_data,  # certId
        dummy_data,  # xs_subnet_tx
        dummy_data,  # xs_subnet_inclusion_proof
        encoded_token_params,
        dummy_data,  # empty field
        {"from": accounts[0]},
    )


def switch_network(subnet_network):
    network.disconnect()
    if subnet_network == "A":
        network.connect("substrate-subnet-network-A")
    if subnet_network == "B":
        network.connect("substrate-subnet-network-B")
