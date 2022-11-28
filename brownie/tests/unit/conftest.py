import brownie
import eth_abi
import pytest


@pytest.fixture(scope="function", autouse=True)
def isolate(fn_isolation):
    # perform a chain rewind after completing each test,
    # to ensure proper isolation
    # https://eth-brownie.readthedocs.io/en/v1.10.3/tests-pytest-intro.html#isolation-fixtures
    pass


@pytest.fixture(scope="module")
def topos_core_contract_A(ToposCoreContract, TokenDeployer, accounts):
    subnet_A_id = brownie.convert.to_bytes("0x01", "bytes32")
    admin_threshold = 1

    token_deployer = TokenDeployer.deploy({"from": accounts[0]})
    topos_core_contract = ToposCoreContract.deploy(
        token_deployer.address, subnet_A_id, {"from": accounts[0]}
    )
    topos_core_contract.setup(
        eth_abi.encode_abi(
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
