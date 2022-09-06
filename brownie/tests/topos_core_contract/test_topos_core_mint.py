import brownie


def test_subnet_id_mismatch_reverts(
    asset_sending,
    recipient_asset_id,
    alice,
    bob,
    recipient_subnet_id,
    cross_subnet_msg_inbound,
    certificate,
    token,
):
    alice_balance = asset_sending.balanceOf(alice)
    amount = alice_balance // 4
    mismatched_subnet_id = 3
    cross_subnet_message = [
        mismatched_subnet_id,
        [[recipient_subnet_id, recipient_asset_id, bob, amount]],
        cross_subnet_msg_inbound,
    ]
    with brownie.reverts("Subnet ID is invalid"):
        token.mint(certificate, cross_subnet_message, {"from": alice})


def test_cross_subnet_msg_type_mismatch_reverts(
    asset_sending,
    recipient_asset_id,
    alice,
    bob,
    initial_subnet_id,
    recipient_subnet_id,
    certificate,
    token,
):
    alice_balance = asset_sending.balanceOf(alice)
    amount = alice_balance // 4
    mismatched_type = 3
    cross_subnet_message = [
        initial_subnet_id,
        [[recipient_subnet_id, recipient_asset_id, bob, amount]],
        mismatched_type,
    ]
    with brownie.reverts("Type of cross-subnet message is invalid"):
        token.mint(certificate, cross_subnet_message, {"from": alice})


def test_certificate_applied_event_fires(
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
    tx = token.mint(certificate, cross_subnet_message, {"from": alice})
    assert len(tx.events) == 5
    assert tx.events["CertificateApplied"].values() == [True]
