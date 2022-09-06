import brownie


def test_balance_decrease(alice, token):
    alice_balance = token.balanceOf(alice)
    amount = alice_balance // 4
    token.burn(alice, amount, {"from": alice})
    assert token.balanceOf(alice) == alice_balance - amount


def test_total_supply_decrease(alice, token):
    total_supply = token.totalSupply()
    alice_balance = token.balanceOf(alice)
    amount = alice_balance // 4
    token.burn(alice, amount, {"from": alice})
    assert token.totalSupply() == total_supply - amount


def test_zero_address_burn_reverts(alice, token):
    alice_balance = token.balanceOf(alice)
    amount = alice_balance // 4
    with brownie.reverts("ERC20: burn from the zero address"):
        token.burn(brownie.ZERO_ADDRESS, amount, {"from": alice})


def test_insufficient_balance_reverts(alice, bob, token):
    alice_balance = token.balanceOf(alice)
    amount = alice_balance // 4
    with brownie.reverts("ERC20: burn amount exceeds balance"):
        token.burn(bob, amount, {"from": alice})


def test_transfer_event_fires(alice, token):
    alice_balance = token.balanceOf(alice)
    amount = alice_balance // 4
    tx = token.burn(alice, amount, {"from": alice})
    assert len(tx.events) == 1
    assert tx.events["Transfer"].values() == [
        alice,
        brownie.ZERO_ADDRESS,
        amount,
    ]


def test_burn_from_non_validator_fails(alice, bob, token):
    alice_balance = token.balanceOf(alice)
    amount = alice_balance // 4
    with brownie.reverts("onlyValidator: bad role"):
        token.burn(alice, amount, {"from": bob})
