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
    recipient_asset_id,
    alice,
    bob,
    initial_subnet_id,
    recipient_subnet_id,
    cross_subnet_msg_inbound,
    certificate,
    token,
):
    alice_balance = asset_sending.balanceOf(alice)
    amount = alice_balance // 4
    cross_subnet_message = [
        initial_subnet_id,
        [[recipient_subnet_id, recipient_asset_id, bob, amount]],
        cross_subnet_msg_inbound,
    ]
    token.mint(certificate, cross_subnet_message, {"from": alice})
    recipient_asset_address = token.getAssetAddress(recipient_asset_id)
    token.claimTransfer(recipient_asset_address, {"from": bob})
    assert token.claimableBalances(recipient_asset_address, bob) == 0


def test_transfer_event_fires(
    asset_sending,
    recipient_asset_id,
    alice,
    bob,
    initial_subnet_id,
    recipient_subnet_id,
    cross_subnet_msg_inbound,
    certificate,
    token,
):
    alice_balance = asset_sending.balanceOf(alice)
    amount = alice_balance // 4
    cross_subnet_message = [
        initial_subnet_id,
        [[recipient_subnet_id, recipient_asset_id, bob, amount]],
        cross_subnet_msg_inbound,
    ]
    token.mint(certificate, cross_subnet_message, {"from": alice})
    recipient_asset_address = token.getAssetAddress(recipient_asset_id)
    tx = token.claimTransfer(recipient_asset_address, {"from": bob})
    assert len(tx.events) == 1
    assert tx.events["Transfer"].values() == [
        brownie.ZERO_ADDRESS,
        bob,
        amount,
    ]


def test_receiver_minted_balance_change(
    asset_sending,
    recipient_asset_id,
    alice,
    bob,
    initial_subnet_id,
    recipient_subnet_id,
    cross_subnet_msg_inbound,
    certificate,
    token,
):
    alice_balance = asset_sending.balanceOf(alice)
    amount = alice_balance // 4
    cross_subnet_message = [
        initial_subnet_id,
        [[recipient_subnet_id, recipient_asset_id, bob, amount]],
        cross_subnet_msg_inbound,
    ]
    token.mint(certificate, cross_subnet_message, {"from": alice})
    recipient_asset_address = token.getAssetAddress(recipient_asset_id)
    token.claimTransfer(recipient_asset_address, {"from": bob})
    recipient_asset = brownie.Asset.at(recipient_asset_address)
    assert recipient_asset.balanceOf(bob) == amount
