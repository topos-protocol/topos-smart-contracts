import brownie
import eth_abi
import pytest


@pytest.fixture(scope="function", autouse=True)
def isolate(fn_isolation):
    # perform a chain rewind after completing each test,
    # to ensure proper isolation
    # https://eth-brownie.readthedocs.io/en/v1.10.3/tests-pytest-intro.html#isolation-fixtures
    pass


def deploy_topos_core_contract(
    accounts, subnet_id, TokenDeployer, ToposCoreContract
):
    admin_threshold = 1
    token_deployer = TokenDeployer.deploy({"from": accounts[0]})
    topos_core_contract = ToposCoreContract.deploy(
        token_deployer.address, subnet_id, {"from": accounts[0]}
    )
    topos_core_contract.setup(
        eth_abi.encode(
            ["address[]", "uint256"],
            [[accounts[0].address], admin_threshold],
        ),
        {"from": accounts[0]},
    )
    return topos_core_contract


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
def topos_core_contract_A(accounts, TokenDeployer, ToposCoreContract):
    subnet_A_id = brownie.convert.to_bytes("0x01", "bytes32")
    return deploy_topos_core_contract(
        accounts, subnet_A_id, TokenDeployer, ToposCoreContract
    )


@pytest.fixture(scope="module")
def topos_core_contract_B(ToposCoreContract, TokenDeployer, accounts):
    subnet_B_id = brownie.convert.to_bytes("0x02", "bytes32")
    return deploy_topos_core_contract(
        accounts, subnet_B_id, TokenDeployer, ToposCoreContract
    )


@pytest.fixture(scope="module")
def topos_executable(accounts, ToposExecutable, topos_core_contract_B):
    return ToposExecutable.deploy(
        topos_core_contract_B.address, {"from": accounts[0]}
    )


@pytest.fixture(scope="module")
def tce_node_registrator(accounts, TCENodeRegistrator):
    tce_node_registrator = TCENodeRegistrator.deploy({"from": accounts[0]})
    return tce_node_registrator
