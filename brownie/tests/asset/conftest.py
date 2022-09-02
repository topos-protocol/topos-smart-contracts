import pytest


@pytest.fixture(scope="function", autouse=True)
def isolate(fn_isolation):
    # perform a chain rewind after completing each test,
    # to ensure proper isolation
    # https://eth-brownie.readthedocs.io/en/v1.10.3/tests-pytest-intro.html#isolation-fixtures
    pass


@pytest.fixture(scope="module")
def token(Asset, accounts):
    return Asset.deploy("Test Token", "TST", 1e23, {"from": accounts[0]})


@pytest.fixture(scope="session")
def alice(accounts):
    yield accounts[0]


@pytest.fixture(scope="session")
def bob(accounts):
    yield accounts[1]


@pytest.fixture(scope="session")
def charlie(accounts):
    yield accounts[2]
