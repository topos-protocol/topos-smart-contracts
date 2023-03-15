import brownie
import eth_abi
import logging
import pytest

from brownie import (
    accounts,
    interface,
    ConstAddressDeployer,
    network,
    TokenDeployer,
    ToposCore,
    ToposCoreProxy,
)

LOGGER = logging.getLogger(__name__)

deploy_token_params = [
    "string",
    "string",
    "uint256",
    "address",
    "uint256",
]
deploy_token_calldata = [
    "Token",
    "Token",
    2**50,
    brownie.ZERO_ADDRESS,
    2**10,
]


# Test to verify that contracts are deployed on multiple networks
# with the same addresses
@pytest.mark.skip_coverage
def test_constant_address_deployment():
    LOGGER.info("Switching to subnet network A")
    switch_network("A")
    _, topos_core_A, _ = deploy_token_deployer(
        brownie.convert.to_bytes("0x01", "bytes32")  # subnet Id
    )
    tokenAParams = eth_abi.encode(deploy_token_params, deploy_token_calldata)
    tokenATx = topos_core_A.deployToken(tokenAParams, {"from": accounts[0]})
    tokenAAddress = tokenATx.events["TokenDeployed"]["tokenAddress"]
    LOGGER.info(f"TestToken address: {tokenAAddress}")

    LOGGER.info("Switching to subnet network B")
    switch_network("B")
    _, topos_core_B, _ = deploy_token_deployer(
        brownie.convert.to_bytes("0x02", "bytes32")
    )
    tokenBParams = eth_abi.encode(deploy_token_params, deploy_token_calldata)
    tokenBTx = topos_core_B.deployToken(tokenBParams, {"from": accounts[0]})
    tokenBAddress = tokenBTx.events["TokenDeployed"]["tokenAddress"]
    LOGGER.info(f"TestToken address: {tokenBAddress}")
    assert tokenAAddress == tokenBAddress


def deploy_token_deployer(network_subnet_id):
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
    topos_core_impl = ToposCore.deploy(
        token_deployer_address,
        {"from": accounts[0]},
    )
    LOGGER.info(f"ToposCore address: {topos_core_impl.address}")
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
    return (
        token_deployer_address,
        topos_core,
        const_address_deployer,
    )


def switch_network(subnet_network):
    network.disconnect()
    if subnet_network == "A":
        network.connect("development")
    if subnet_network == "B":
        network.connect("development-two")
