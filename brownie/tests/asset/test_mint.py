import brownie


def test_balance_increase(alice, token):
    alice_balance = token.balanceOf(alice)
    amount = alice_balance // 4
    token.mint(alice, amount, {"from": alice})
    assert token.balanceOf(alice) == alice_balance + amount


def test_total_supply_increase(alice, token):
    total_supply = token.totalSupply()
    alice_balance = token.balanceOf(alice)
    amount = alice_balance // 4
    token.mint(alice, amount, {"from": alice})
    assert token.totalSupply() == total_supply + amount


def test_zero_address_mint_reverts(alice, token):
    alice_balance = token.balanceOf(alice)
    amount = alice_balance // 4
    with brownie.reverts():
        token.mint(brownie.ZERO_ADDRESS, amount, {"from": alice})


def test_transfer_event_fires(alice, token):
    alice_balance = token.balanceOf(alice)
    amount = alice_balance // 4
    tx = token.mint(alice, amount, {"from": alice})
    assert len(tx.events) == 1
    assert tx.events["Transfer"].values() == [
        brownie.ZERO_ADDRESS,
        alice,
        amount,
    ]
