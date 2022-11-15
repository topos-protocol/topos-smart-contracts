import brownie
import eth_abi
from brownie import (
    TokenDeployer,
    ToposCoreContract,
    ConstAddressDeployer,
    accounts,
    network,
)
import logging

LOGGER = logging.getLogger(__name__)

alice_private = (
    "0x99B3C12287537E38C90A9219D4CB074A89A16E9CDB20BF85728EBD97C343E342"
)
bob_private = (
    "0x8075991ce870b93a8870eca0c0f91913d12f47948ca0fd25b49c6fa7cdbeee8b"
)
deploy_token_params = [
    "string",
    "string",
    "uint8",
    "uint256",
    "address",
    "uint256",
]
deploy_token_calldata = [
    "Token",
    "Token",
    18,
    2**50,
    brownie.ZERO_ADDRESS,
    2**10,
]


# Test to verify that contracts are deployed on multiple networks
# with the same addresses
def test_constant_address_deployment():
    LOGGER.info("Switching to subnet network A")
    LOGGER.info(f"admin account: {accounts[0]}")
    LOGGER.info(f"admin account nonce: {accounts[0].nonce}")
    LOGGER.info(f"bob account: {accounts[1]}")
    LOGGER.info(f"bob account nonce: {accounts[1].nonce}")
    switch_network("A")
    _, topos_core_contract_A, _ = deploy_token_deployer(
        brownie.convert.to_bytes("0x01", "bytes32")  # subnet Id
    )
    tokenAParams = eth_abi.encode(deploy_token_params, deploy_token_calldata)
    tokenATx = topos_core_contract_A.deployToken(
        tokenAParams, {"from": accounts[0]}
    )
    tokenAAddress = tokenATx.events["TokenDeployed"]["tokenAddresses"]
    LOGGER.info(f"TestToken address: {tokenAAddress}")

    LOGGER.info("Switching to subnet network B")
    switch_network("B")
    LOGGER.info(f"admin account: {accounts[0]}")
    LOGGER.info(f"admin account nonce: {accounts[0].nonce}")
    LOGGER.info(f"bob account: {accounts[1]}")
    LOGGER.info(f"bob account nonce: {accounts[1].nonce}")
    _, topos_core_contract_B, _ = deploy_token_deployer(
        brownie.convert.to_bytes("0x02", "bytes32")
    )
    tokenBParams = eth_abi.encode(deploy_token_params, deploy_token_calldata)
    tokenBTx = topos_core_contract_B.deployToken(
        tokenBParams, {"from": accounts[0]}
    )
    tokenBAddress = tokenBTx.events["TokenDeployed"]["tokenAddresses"]
    LOGGER.info(f"TestToken address: {tokenBAddress}")
    assert tokenAAddress == tokenBAddress


def deploy_token_deployer(networkSubnetId):
    # accounts.add(alice_private)
    # accounts.add(bob_private)
    const_address_deployer = ConstAddressDeployer.deploy({"from": accounts[0]})
    LOGGER.info(
        f"ConstantAddressDeployer address: {const_address_deployer.address}"
    )
    const_address_deployer_tx = const_address_deployer.deploy(
        TokenDeployer.bytecode,
        brownie.convert.to_bytes("0xf7", "bytes32"),
        {"from": accounts[0]},
    )
    token_deployer_address = const_address_deployer_tx.events["Deployed"][
        "deployedAddress"
    ]
    LOGGER.info(f"TokenDeployer address: {token_deployer_address}")
    topos_core_contract = ToposCoreContract.deploy(
        token_deployer_address,
        networkSubnetId,
        {"from": accounts[0]},
    )
    LOGGER.info(f"ToposCoreContract address: {topos_core_contract.address}")
    return (
        token_deployer_address,
        topos_core_contract,
        const_address_deployer,
    )


def switch_network(subnet_network):
    network.disconnect()
    if subnet_network == "A":
        network.connect("development")
    if subnet_network == "B":
        network.connect("development-two")
