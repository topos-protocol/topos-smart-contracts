import brownie


def test_amount_zero_reverts(
    asset_sending, asset_recipient, alice, bob, terminal_subnet_id, token
):
    alice_balance = asset_sending.balanceOf(alice)
    amount = alice_balance // 4
    asset_sending.approve(token.address, amount, {"from": alice})

    with brownie.reverts("Amount cannot be zero"):
        token.sendToken(
            asset_sending.address,
            terminal_subnet_id,
            asset_recipient.address,
            bob,
            0,
            {"from": alice},
        )


def test_sent_event_fires(
    asset_sending, asset_recipient, alice, bob, terminal_subnet_id, token
):
    alice_balance = asset_sending.balanceOf(alice)
    amount = alice_balance // 4

    asset_sending.approve(token.address, amount, {"from": alice})
    tx = token.sendToken(
        asset_sending.address,
        terminal_subnet_id,
        asset_recipient.address,
        bob,
        amount,
        {"from": alice},
    )

    assert len(tx.events) == 3  # ["Approval"], ["Transfer"], ["Sent"]
    assert tx.events["Sent"].values() == [
        terminal_subnet_id,
        asset_recipient.address,
        bob,
        amount,
    ]
