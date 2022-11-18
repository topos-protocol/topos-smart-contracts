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
def topos_contracts(
    ToposCoreContract, TokenDeployer, ToposExecutable, accounts
):
    subnet_id = brownie.convert.to_bytes("0x02", "bytes32")
    admin_threshold = 1

    token_deployer = TokenDeployer.deploy({"from": accounts[0]})
    topos_core_contract = ToposCoreContract.deploy(
        token_deployer.address, subnet_id, {"from": accounts[0]}
    )
    topos_core_contract.setup(
        eth_abi.encode_abi(
            ["address[]", "uint256"],
            [[accounts[0].address], admin_threshold],
        ),
        {"from": accounts[0]},
    )

    topos_executable = ToposExecutable.deploy(
        topos_core_contract.address, {"from": accounts[0]}
    )
    return topos_core_contract, topos_executable


@pytest.fixture(scope="session")
def admin(accounts):
    yield accounts[0]


@pytest.fixture(scope="session")
def alice(accounts):
    yield accounts[1]
