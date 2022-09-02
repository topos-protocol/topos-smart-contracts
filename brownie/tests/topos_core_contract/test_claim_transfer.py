import brownie


def test_no_claim_amount_reverts(
    asset_recipient,
    bob,
    token,
):
    with brownie.reverts("No amount to claim"):
        token.claimTransfer(asset_recipient.address, {"from": bob})


def test_recipient_balance_decreases(
    asset_sending,
    asset_recipient,
    alice,
    bob,
    initial_subnet_id,
    terminal_subnet_id,
    cross_subnet_msg_inbound,
    certificate,
    token,
):
    alice_balance = asset_sending.balanceOf(alice)
    amount = alice_balance // 4
    cross_subnet_message = [
        initial_subnet_id,
        [[terminal_subnet_id, asset_recipient.address, bob, amount]],
        cross_subnet_msg_inbound,
    ]
    token.mint(certificate, cross_subnet_message, {"from": alice})
    token.claimTransfer(asset_recipient.address, {"from": bob})
    assert token.balances(asset_recipient.address, bob) == 0


def test_transfer_event_fires(
    asset_sending,
    asset_recipient,
    alice,
    bob,
    initial_subnet_id,
    terminal_subnet_id,
    cross_subnet_msg_inbound,
    certificate,
    token,
):
    alice_balance = asset_sending.balanceOf(alice)
    amount = alice_balance // 4
    cross_subnet_message = [
        initial_subnet_id,
        [[terminal_subnet_id, asset_recipient.address, bob, amount]],
        cross_subnet_msg_inbound,
    ]
    token.mint(certificate, cross_subnet_message, {"from": alice})
    tx = token.claimTransfer(asset_recipient.address, {"from": bob})
    assert len(tx.events) == 1
    assert tx.events["Transfer"].values() == [
        brownie.ZERO_ADDRESS,
        bob,
        amount,
    ]
