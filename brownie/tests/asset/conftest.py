import pytest


@pytest.fixture(scope="function", autouse=True)
def isolate(fn_isolation):
    # perform a chain rewind after completing each test,
    # to ensure proper isolation
    # https://eth-brownie.readthedocs.io/en/v1.10.3/tests-pytest-intro.html#isolation-fixtures
    pass


@pytest.fixture(scope="module")
def token(Asset, accounts):
    asset = Asset.deploy({"from": accounts[0]})
    asset.initialize(
        "Test Token",
        "TST",
        1e23,
        accounts[0],
        accounts[0],
        {"from": accounts[0]},
    )  # Alice is made the default owner of the deployed contract
    return asset


@pytest.fixture(scope="session")
def alice(accounts):
    yield accounts[0]


@pytest.fixture(scope="session")
def bob(accounts):
    yield accounts[1]


@pytest.fixture(scope="session")
def charlie(accounts):
    yield accounts[2]
