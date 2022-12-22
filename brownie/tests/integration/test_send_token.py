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
    ToposCoreContract,
    ToposCoreContractProxy,
)

LOGGER = logging.getLogger(__name__)

# Constants
approve_amount = 50
daily_mint_limit = 100
dummy_cert_position = 12
dummy_cert_id = brownie.convert.to_bytes("0xdeaf", "bytes")
dummy_data = brownie.convert.to_bytes("0x00", "bytes")
mint_amount = 100
mint_cap = 1000
send_amount = 50
subnet_A_id = brownie.convert.to_bytes("0x01", "bytes32")
subnet_B_id = brownie.convert.to_bytes("0x02", "bytes32")
token_symbol = "TKX"


@pytest.mark.skip_coverage
def test_send_token():
    # Network A
    LOGGER.info("Switching to subnet network A")
    switch_network("A")
    deploy_initial_contracts(subnet_A_id)
    token_sent_event = send_token()

    # Event logs as seen by the automation web-service
    sender = token_sent_event["sender"]
    sourceSubnetId = token_sent_event["sourceSubnetId"]
    targetSubnetId = token_sent_event["targetSubnetId"]
    receiver = token_sent_event["receiver"]
    symbol = token_sent_event["symbol"]
    amount = token_sent_event["amount"]

    # Network B
    LOGGER.info("Switching to subnet network B")
    switch_network("B")
    deploy_initial_contracts(subnet_B_id)
    # if you don't validate a cert then the mint function would fail
    validate_dummy_cert(topos_core_contract_B)
    mint_token(
        topos_core_contract_B,
        dummy_data,  # tx_hash
        sender,
        sourceSubnetId,
        targetSubnetId,
        receiver,
        symbol,
        amount,
    )
    token_address = topos_core_contract_B.tokenAddresses(token_symbol)
    burnable_mint_erc20_B = BurnableMintableCappedERC20.at(token_address)
    fast_forward_nonce(1)
    assert burnable_mint_erc20_B.balanceOf(receiver) == send_amount


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
    topos_core_contract_impl = ToposCoreContract.deploy(
        token_deployer_address,
        network_subnet_id,
        {"from": accounts[0]},
    )
    LOGGER.info(
        "ToposCoreContract implementation address:"
        + f"{topos_core_contract_impl.address}"
    )

    # set admin for ToposCoreContract
    admin_threshold = 1
    setup_params = eth_abi.encode(
        ["address[]", "uint256"],
        [[accounts[0].address], admin_threshold],
    )

    # deploy ToposCoreContractProxy
    topos_core_contract_proxy = ToposCoreContractProxy.deploy(
        topos_core_contract_impl.address,
        setup_params,
        {"from": accounts[0]},
    )
    LOGGER.info(
        f"ToposCoreContractProxy address: {topos_core_contract_proxy.address}"
    )
    topos_core_contract = interface.IToposCoreContract(
        topos_core_contract_proxy.address
    )

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

    deploy_token_tx = topos_core_contract.deployToken(
        encoded_token_params, {"from": accounts[0]}
    )
    LOGGER.info(
        "TokenX address: "
        + f"{deploy_token_tx.events['TokenDeployed']['tokenAddresses']}"
    )

    if network_subnet_id == subnet_A_id:
        # mint some amount for the sender
        # we don't need to do this for pre-existing tokens, given that
        # the sender has some balance to transfer in his/her account
        topos_core_contract.giveToken(
            token_symbol, accounts[0], mint_amount, {"from": accounts[0]}
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


def validate_dummy_cert(topos_core_contract):
    cert_params = ["bytes", "uint256"]
    cert_values = [dummy_cert_id, dummy_cert_position]
    encoded_cert_params = eth_abi.encode(cert_params, cert_values)
    topos_core_contract.verifyCertificate(
        encoded_cert_params, {"from": accounts[0]}
    )


def mint_token(
    topos_core_contract,
    tx_hash,
    sender,
    source_subnet_id,
    target_subnet_id,
    receiver,
    symbol,
    amount,
):
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
        tx_hash,
        sender,
        source_subnet_id,
        target_subnet_id,
        receiver,
        symbol,
        amount,
    ]
    encoded_token_params = eth_abi.encode(mint_token_params, mint_token_values)
    topos_core_contract.executeAssetTransfer(
        dummy_cert_id,  # certId
        encoded_token_params,
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
