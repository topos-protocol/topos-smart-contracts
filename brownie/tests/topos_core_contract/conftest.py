import pytest


@pytest.fixture(scope="function", autouse=True)
def isolate(fn_isolation):
    # perform a chain rewind after completing each test,
    # to ensure proper isolation
    # https://eth-brownie.readthedocs.io/en/v1.10.3/tests-pytest-intro.html#isolation-fixtures
    pass


@pytest.fixture(scope="module")
def token(ToposCoreContract, accounts):
    # Alice is the owner of ToposCoreContract
    return ToposCoreContract.deploy(1, {"from": accounts[0]})


@pytest.fixture(scope="module")
def asset_sending(Asset, token, accounts):
    asset = Asset.deploy({"from": accounts[0]})
    asset.initialize(
        "Test Token Sending",
        "TSTS",
        1e23,
        accounts[0],
        token.address,
        {"from ": accounts[0]},
    )
    return asset


@pytest.fixture(scope="module")
def asset_recipient(Asset, token, accounts):
    asset = Asset.deploy({"from": accounts[0]})
    asset.initialize(
        "Test Token Recipient",
        "TSTR",
        1e23,
        accounts[0],
        token.address,
        {"from ": accounts[0]},
    )
    return asset


@pytest.fixture(scope="session")
def alice(accounts):
    yield accounts[0]


@pytest.fixture(scope="session")
def bob(accounts):
    yield accounts[1]


@pytest.fixture(scope="session")
def initial_subnet_id():
    yield 1


@pytest.fixture(scope="session")
def recipient_subnet_id():
    yield 2


@pytest.fixture(scope="session")
def recipient_asset_id():
    yield "RECIPIENT_ASSET"


@pytest.fixture(scope="session")
def cross_subnet_msg_inbound():
    yield 0


@pytest.fixture(scope="session")
def certificate():
    yield 0x00  # empty certificate
