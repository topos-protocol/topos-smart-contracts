import brownie
import eth_abi
import logging
import pytest

from brownie import (
    accounts,
    interface,
    BurnableMintableCappedERC20,
    ConstAddressDeployer,
    network,
    TokenDeployer,
    ToposCore,
    ToposCoreProxy,
)
from fetch_transaction import get_raw_transaction_positional_args

LOGGER = logging.getLogger(__name__)

# Constants
approve_amount = 50
daily_mint_limit = 100
dummy_cert_position = 12
dummy_cert_id = brownie.convert.to_bytes("0xdeaf", "bytes32")
dummy_data = brownie.convert.to_bytes("0x00", "bytes")
dummy_hash = brownie.convert.to_bytes("0x0004", "bytes32")
mint_amount = 100
mint_cap = 1000
send_amount = 50
subnet_A_id = brownie.convert.to_bytes("0x01", "bytes32")
subnet_B_id = brownie.convert.to_bytes("0x02", "bytes32")
token_symbol = "TKX"
verifier = 1


@pytest.mark.skip_coverage
def test_send_token():
    # Network A
    LOGGER.info("Switching to subnet network A")
    switch_network("A")
    deploy_initial_contracts(subnet_A_id)
    index_of_data_in_tx_raw, tx_raw = send_token()

    # Network B
    LOGGER.info("Switching to subnet network B")
    switch_network("B")
    deploy_initial_contracts(subnet_B_id)
    # if you don't validate a cert then the mint function would fail
    push_dummy_cert(topos_core_B)
    mint_token(topos_core_B, index_of_data_in_tx_raw, tx_raw)
    token = topos_core_B.getTokenBySymbol(token_symbol)
    burnable_mint_erc20_B = BurnableMintableCappedERC20.at(
        token["tokenAddress"]
    )
    fast_forward_nonce(1)
    assert burnable_mint_erc20_B.balanceOf(accounts[1]) == send_amount


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

    # deploy ToposCore
    topos_core_impl = ToposCore.deploy(
        token_deployer_address,
        network_subnet_id,
        {"from": accounts[0]},
    )
    LOGGER.info(
        "ToposCore implementation address:" + f"{topos_core_impl.address}"
    )

    # set admin for ToposCore
    admin_threshold = 1
    setup_params = eth_abi.encode(
        ["address[]", "uint256"],
        [[accounts[0].address], admin_threshold],
    )

    # deploy ToposCoreProxy
    topos_core_proxy = ToposCoreProxy.deploy(
        topos_core_impl.address,
        setup_params,
        {"from": accounts[0]},
    )
    LOGGER.info(f"ToposCoreProxy address: {topos_core_proxy.address}")
    topos_core = interface.IToposCore(topos_core_proxy.address)

    # deploy a token
    token_params = [
        "string",
        "string",
        "uint256",
        "address",
        "uint256",
    ]
    token_values = [
        "TokenX",
        token_symbol,
        mint_cap,
        brownie.ZERO_ADDRESS,
        daily_mint_limit,
    ]
    encoded_token_params = eth_abi.encode(token_params, token_values)

    deploy_token_tx = topos_core.deployToken(
        encoded_token_params, {"from": accounts[0]}
    )
    LOGGER.info(
        "TokenX address: "
        + f"{deploy_token_tx.events['TokenDeployed']['tokenAddress']}"
    )

    if network_subnet_id == subnet_A_id:
        # mint some amount for the sender
        # we don't need to do this for pre-existing tokens, given that
        # the sender has some balance to transfer in his/her account
        topos_core.giveToken(
            token_symbol, accounts[0], mint_amount, {"from": accounts[0]}
        )
        # get ERC20 contract at the deployed address
        burnable_mint_erc20 = BurnableMintableCappedERC20.at(
            deploy_token_tx.events["TokenDeployed"]["tokenAddress"]
        )
        # approve toposCore to spend on behalf of the sender
        burnable_mint_erc20.approve(
            topos_core, approve_amount, {"from": accounts[0]}
        )
        global topos_core_A
        topos_core_A = topos_core
    if network_subnet_id == subnet_B_id:
        global topos_core_B
        topos_core_B = topos_core


def send_token():
    tx = topos_core_A.sendToken(
        subnet_B_id,
        accounts[1],
        token_symbol,
        send_amount,
        {"from": accounts[0]},
    )
    tx_raw = get_raw_transaction_positional_args(
        "http://127.0.0.1:8545", tx.txid
    )
    index_of_data_in_tx_raw = int(
        tx_raw.index(tx.input[2:]) / 2
    )  # [2:] removes 0x prefix
    # LOGGER.info(f"TRANSACTION HEX: {tx_raw}")
    # LOGGER.info(f"TRANSACTION HASH: {tx.txid}")
    # LOGGER.info(f"TRANSACTION INDEX: {index}")
    return (index_of_data_in_tx_raw, tx_raw)


def push_dummy_cert(topos_core):
    cert_params = [
        "bytes32",
        "bytes32",
        "bytes32",
        "bytes32",
        "bytes32[]",
        "uint32",
        "bytes32",
        "bytes",
        "bytes",
    ]
    cert_values = [
        dummy_cert_id,
        subnet_A_id,
        dummy_hash,
        dummy_hash,
        [subnet_B_id],
        verifier,
        dummy_cert_id,
        dummy_data,
        dummy_data,
    ]
    encoded_cert_params = eth_abi.encode(cert_params, cert_values)
    topos_core.pushCertificate(
        encoded_cert_params, dummy_cert_position, {"from": accounts[0]}
    )


def mint_token(topos_core, index_of_data_in_tx_raw, tx_raw):
    topos_core.executeAssetTransfer(
        dummy_cert_id,  # certId
        index_of_data_in_tx_raw,
        tx_raw,
        dummy_data,  # xs_subnet_inclusion_proof
        {"from": accounts[0]},
    )


def fast_forward_nonce(times):
    for _ in range(times):
        accounts[0].transfer(accounts[1], "10 ether")


def switch_network(subnet_network):
    network.disconnect()
    if subnet_network == "A":
        network.connect("development")
    if subnet_network == "B":
        network.connect("development-two")
