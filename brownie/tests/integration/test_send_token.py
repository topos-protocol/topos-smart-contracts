import brownie
import eth_abi
import json
import logging
import pytest
import subprocess


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

LOGGER = logging.getLogger(__name__)

# Constants
APPROVE_AMOUNT = 50
DAILY_MINT_LIMIT = 100
DUMMY_CERT_POSITION = 12
DUMMY_CERT_ID = brownie.convert.to_bytes("0xdeaf", "bytes32")
DUMMY_DATA = brownie.convert.to_bytes("0x00", "bytes")
DUMMY_HASH = brownie.convert.to_bytes("0x0004", "bytes32")
END_POINT = "http://127.0.0.1:8545"
MINT_AMOUNT = 100
MINT_CAP = 1000
SEND_AMOUNT = 50
SCRIPT_PATH = "brownie/tests/integration/generate_merkle_proof.py"
SUBNET_A_ID = brownie.convert.to_bytes("0x01", "bytes32")
SUBNET_B_ID = brownie.convert.to_bytes("0x02", "bytes32")
TOKEN_SYMBOL = "TKX"
VERIFIER = 1


@pytest.mark.skip_coverage
def test_send_token():
    # Network A
    LOGGER.info("Switching to subnet network A")
    switch_network("A")
    deploy_initial_contracts(SUBNET_A_ID)
    index_of_data_in_tx_raw, proof_blob, tx_raw, tx_root = send_token()

    # Network B
    LOGGER.info("Switching to subnet network B")
    switch_network("B")
    deploy_initial_contracts(SUBNET_B_ID)
    # if you don't validate a cert then the mint function would fail
    push_dummy_cert(topos_core_B, tx_root)
    mint_token(
        topos_core_B, index_of_data_in_tx_raw, proof_blob, tx_raw, tx_root
    )
    token = topos_core_B.getTokenBySymbol(TOKEN_SYMBOL)
    burnable_mint_erc20_B = BurnableMintableCappedERC20.at(
        token["tokenAddress"]
    )
    fast_forward_nonce(1)
    assert burnable_mint_erc20_B.balanceOf(accounts[1]) == SEND_AMOUNT


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
    topos_core.setNetworkSubnetId(network_subnet_id, {"from": accounts[0]})

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
        TOKEN_SYMBOL,
        MINT_CAP,
        brownie.ZERO_ADDRESS,
        DAILY_MINT_LIMIT,
    ]
    encoded_token_params = eth_abi.encode(token_params, token_values)

    deploy_token_tx = topos_core.deployToken(
        encoded_token_params, {"from": accounts[0]}
    )
    LOGGER.info(
        "TokenX address: "
        + f"{deploy_token_tx.events['TokenDeployed']['tokenAddress']}"
    )

    if network_subnet_id == SUBNET_A_ID:
        # mint some amount for the sender
        # we don't need to do this for pre-existing tokens, given that
        # the sender has some balance to transfer in his/her account
        topos_core.giveToken(
            TOKEN_SYMBOL, accounts[0], MINT_AMOUNT, {"from": accounts[0]}
        )
        # get ERC20 contract at the deployed address
        burnable_mint_erc20 = BurnableMintableCappedERC20.at(
            deploy_token_tx.events["TokenDeployed"]["tokenAddress"]
        )
        # approve toposCore to spend on behalf of the sender
        burnable_mint_erc20.approve(
            topos_core, APPROVE_AMOUNT, {"from": accounts[0]}
        )
        global topos_core_A
        topos_core_A = topos_core
    if network_subnet_id == SUBNET_B_ID:
        global topos_core_B
        topos_core_B = topos_core


def send_token():
    tx = topos_core_A.sendToken(
        SUBNET_B_ID,
        accounts[1],
        TOKEN_SYMBOL,
        SEND_AMOUNT,
        {"from": accounts[0]},
    )
    # Run as a subprocess to avoid dependency clash
    result = subprocess.run(
        ["python3", SCRIPT_PATH, END_POINT, tx.txid], stdout=subprocess.PIPE
    ).stdout.decode("utf-8")
    json_str = json.loads(result)
    proof_blob = bytes.fromhex(json_str["proof_blob"])
    tx_raw = bytes.fromhex(json_str["tx_raw"])
    tx_root = json_str["txns_root"]
    # The tx_raw and tx.input are represented in hexadecimal
    # format, with each two characters representing one byte.
    # To get the index of the input in tx_raw in terms
    # of bytes, the index of the data in tx.input must be divided
    # by 2.This is because in Solidity, the bytes[i:] syntax
    # returns the bytes starting from the ith byte.
    index_of_data_in_tx_raw = int(
        tx_raw.hex().index(tx.input[2:]) / 2
    )  # [2:] removes 0x prefix
    return (index_of_data_in_tx_raw, proof_blob, tx_raw, tx_root)


def push_dummy_cert(topos_core, tx_root):
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
        DUMMY_CERT_ID,
        SUBNET_A_ID,
        DUMMY_HASH,
        brownie.convert.to_bytes(tx_root, "bytes32"),
        [SUBNET_B_ID],
        VERIFIER,
        DUMMY_CERT_ID,
        DUMMY_DATA,
        DUMMY_DATA,
    ]
    encoded_cert_params = eth_abi.encode(cert_params, cert_values)
    topos_core.pushCertificate(
        encoded_cert_params, DUMMY_CERT_POSITION, {"from": accounts[0]}
    )


def mint_token(
    topos_core, index_of_data_in_tx_raw, proof_blob, tx_raw, tx_root
):
    topos_core.executeAssetTransfer(
        index_of_data_in_tx_raw,
        proof_blob,
        tx_raw,
        tx_root,
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
