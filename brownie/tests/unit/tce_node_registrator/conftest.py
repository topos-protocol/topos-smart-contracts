import pytest


@pytest.fixture(scope="function", autouse=True)
def isolate(fn_isolation):
    # perform a chain rewind after completing each test,
    # to ensure proper isolation
    # https://eth-brownie.readthedocs.io/en/v1.10.3/tests-pytest-intro.html#isolation-fixtures
    pass


@pytest.fixture(scope="module")
def tce_node_registrator(accounts, TCENodeRegistrator):
    tce_node_registrator = TCENodeRegistrator.deploy({"from": accounts[0]})
    return tce_node_registrator


@pytest.fixture(scope="session")
def alice(accounts):
    yield accounts[0]
