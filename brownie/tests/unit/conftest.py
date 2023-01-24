import brownie
import eth_abi
import pytest


@pytest.fixture(scope="function", autouse=True)
def isolate(fn_isolation):
    # perform a chain rewind after completing each test,
    # to ensure proper isolation
    # https://eth-brownie.readthedocs.io/en/v1.10.3/tests-pytest-intro.html#isolation-fixtures
    pass


def deploy_topos_core(
    accounts,
    interface,
    subnet_id,
    TokenDeployer,
    ToposCore,
    ToposCoreProxy,
):
    admin_threshold = 1
    token_deployer = TokenDeployer.deploy({"from": accounts[0]})
    topos_core_impl = ToposCore.deploy(
        token_deployer.address, subnet_id, {"from": accounts[0]}
    )
    topos_core_proxy = ToposCoreProxy.deploy(
        topos_core_impl.address,
        eth_abi.encode(
            ["address[]", "uint256"],
            [[accounts[0].address], admin_threshold],
        ),
        {"from": accounts[0]},
    )
    topos_core = interface.IToposCore(topos_core_proxy.address)

    return topos_core


@pytest.fixture(scope="session")
def admin(accounts):
    yield accounts[0]


@pytest.fixture(scope="session")
def alice(accounts):
    yield accounts[1]


@pytest.fixture(scope="session")
def bob(accounts):
    yield accounts[2]


@pytest.fixture(scope="module")
def subnet_registrator(accounts, SubnetRegistrator):
    subnet_registrator = SubnetRegistrator.deploy({"from": accounts[0]})
    return subnet_registrator


@pytest.fixture(scope="module")
def topos_core_A(
    accounts,
    interface,
    TokenDeployer,
    ToposCore,
    ToposCoreProxy,
):
    subnet_A_id = brownie.convert.to_bytes("0x01", "bytes32")
    return deploy_topos_core(
        accounts,
        interface,
        subnet_A_id,
        TokenDeployer,
        ToposCore,
        ToposCoreProxy,
    )


@pytest.fixture(scope="module")
def topos_core_B(
    accounts,
    interface,
    TokenDeployer,
    ToposCore,
    ToposCoreProxy,
):
    subnet_B_id = brownie.convert.to_bytes("0x02", "bytes32")
    return deploy_topos_core(
        accounts,
        interface,
        subnet_B_id,
        TokenDeployer,
        ToposCore,
        ToposCoreProxy,
    )


@pytest.fixture(scope="module")
def topos_executable(accounts, ToposExecutable, topos_core_B):
    return ToposExecutable.deploy(topos_core_B.address, {"from": accounts[0]})


@pytest.fixture(scope="module")
def tce_node_registrator(accounts, TCENodeRegistrator):
    tce_node_registrator = TCENodeRegistrator.deploy({"from": accounts[0]})
    return tce_node_registrator
