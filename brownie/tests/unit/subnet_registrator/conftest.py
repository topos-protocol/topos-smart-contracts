import pytest


@pytest.fixture(scope="function", autouse=True)
def isolate(fn_isolation):
    # perform a chain rewind after completing each test,
    # to ensure proper isolation
    # https://eth-brownie.readthedocs.io/en/v1.10.3/tests-pytest-intro.html#isolation-fixtures
    pass


@pytest.fixture(scope="module")
def subnet_registrator(accounts, SubnetRegistrator):
    subnet_registrator = SubnetRegistrator.deploy({"from": accounts[0]})
    return subnet_registrator


@pytest.fixture(scope="session")
def alice(accounts):
    yield accounts[0]
