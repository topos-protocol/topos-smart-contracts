import pytest
import brownie


@pytest.mark.parametrize("idx", range(5))
def test_initial_approval_is_zero(accounts, alice, token, idx):
    assert token.allowance(alice, accounts[idx]) == 0


def test_approve(alice, bob, token):
    token.approve(bob, 10**19, {"from": alice})
    assert token.allowance(alice, bob) == 10**19


def test_modify_approve(alice, bob, token):
    token.approve(bob, 10**19, {"from": alice})
    token.approve(bob, 12345678, {"from": alice})
    assert token.allowance(alice, bob) == 12345678


def test_revoke_approve(alice, bob, token):
    token.approve(bob, 10**19, {"from": alice})
    token.approve(bob, 0, {"from": alice})
    assert token.allowance(alice, bob) == 0


def test_approve_self(alice, token):
    token.approve(alice, 10**19, {"from": alice})
    assert token.allowance(alice, alice) == 10**19


def test_only_affects_target(alice, bob, token):
    token.approve(bob, 10**19, {"from": alice})
    assert token.allowance(bob, alice) == 0


def test_returns_true(alice, bob, token):
    tx = token.approve(bob, 10**19, {"from": alice})
    assert tx.return_value is True


def test_approval_event_fires(alice, bob, token):
    tx = token.approve(bob, 10**19, {"from": alice})
    assert len(tx.events) == 1
    assert tx.events["Approval"].values() == [alice, bob, 10**19]


def test_spender_zero_address_reverts(alice, bob, token):
    with brownie.reverts():
        token.approve(brownie.ZERO_ADDRESS, 10**19, {"from": alice})


def test_owner_zero_address_reverts(alice, token):
    with brownie.reverts():
        token.approve(alice, 10**19, {"from": brownie.ZERO_ADDRESS})


def test_decrease_allowance(alice, bob, token):
    token.approve(bob, 10**19, {"from": alice})
    token.decreaseAllowance(bob, 10**19, {"from": alice})
    assert token.allowance(alice, bob) == 0


def test_insufficient_current_allowance_reverts(alice, bob, token):
    token.approve(bob, 10**19, {"from": alice})
    with brownie.reverts():
        token.decreaseAllowance(bob, 10**20, {"from": alice})


def test_decrease_allowance_returns_true(alice, bob, token):
    token.approve(bob, 10**19, {"from": alice})
    tx = token.decreaseAllowance(bob, 10**19, {"from": alice})
    assert tx.return_value is True
