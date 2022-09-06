import brownie


def test_amount_zero_reverts(
    asset_sending, recipient_asset_id, alice, bob, recipient_subnet_id, token
):
    alice_balance = asset_sending.balanceOf(alice)
    amount = alice_balance // 4
    asset_sending.approve(token.address, amount, {"from": alice})
    with brownie.reverts("Amount cannot be zero"):
        token.sendToken(
            asset_sending.address,
            recipient_subnet_id,
            recipient_asset_id,
            alice,
            bob,
            0,
            {"from": alice},
        )


def test_sent_event_fires(
    asset_sending, recipient_asset_id, alice, bob, recipient_subnet_id, token
):
    alice_balance = asset_sending.balanceOf(alice)
    amount = alice_balance // 4
    asset_sending.approve(token.address, amount, {"from": alice})
    tx = token.sendToken(
        asset_sending.address,
        recipient_subnet_id,
        recipient_asset_id,
        alice,
        bob,
        amount,
        {"from": alice},
    )
    assert len(tx.events) == 3  # ["Approval"], ["Transfer"], ["Sent"]
    assert tx.events["Sent"].values() == [
        recipient_subnet_id,
        recipient_asset_id,
        alice,
        bob,
        amount,
    ]
