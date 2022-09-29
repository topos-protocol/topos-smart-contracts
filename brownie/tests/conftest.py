import pytest


@pytest.fixture(scope="function", autouse=True)
def isolate(fn_isolation):
    # perform a chain rewind after completing each test,
    # to ensure proper isolation
    # https://eth-brownie.readthedocs.io/en/v1.10.3/tests-pytest-intro.html#isolation-fixtures
    pass


@pytest.fixture(scope="module")
def sendingContracts(ToposERC20Base, ToposCoreContract, accounts):
    subnetATCC = ToposCoreContract.deploy(
        1, accounts[3], {"from": accounts[0]}
    )
    subnetAToken = ToposERC20Base.deploy(
        "ToposERC20Base",
        "TST",
        1e23,
        subnetATCC.address,
        1,
        {"from": accounts[0]},
    )
    return (subnetAToken, subnetATCC)


@pytest.fixture(scope="module")
def receivingContracts(ToposERC20Base, ToposCoreContract, accounts):
    subnetBTCC = ToposCoreContract.deploy(
        2, accounts[3], {"from": accounts[0]}
    )
    subnetBToken = ToposERC20Base.deploy(
        "ToposERC20Base",
        "TST",
        1e23,
        subnetBTCC.address,
        2,
        {"from": accounts[0]},
    )
    return (subnetBToken, subnetBTCC)


@pytest.fixture(scope="session")
def alice(accounts):
    yield accounts[0]


@pytest.fixture(scope="session")
def bob(accounts):
    yield accounts[1]


@pytest.fixture(scope="session")
def charlie(accounts):
    yield accounts[2]


@pytest.fixture(scope="session")
def subnetAId():
    yield 1


@pytest.fixture(scope="session")
def subnetBId():
    yield 2


@pytest.fixture(scope="session")
def validator(accounts):
    yield accounts[3]


@pytest.fixture(scope="session")
def dummyCertId():
    yield "0x43"


@pytest.fixture(scope="session")
def dummyPrevCertId():
    yield "0x42"


@pytest.fixture(scope="session")
def dummyMsgId():
    yield "0x01"
