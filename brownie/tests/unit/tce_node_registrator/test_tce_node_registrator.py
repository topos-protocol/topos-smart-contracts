import brownie

peer_id = brownie.convert.to_bytes("0xdeaf", "bytes")


def test_register_tce_node_reverts_on_already_registered(
    alice, tce_node_registrator
):
    tce_node_registrator.registerTCENode(peer_id, {"from": alice})
    # should revert since tce node is already registered
    with brownie.reverts():
        tce_node_registrator.registerTCENode(peer_id, {"from": alice})


def test_register_tce_node_emits_event(alice, tce_node_registrator):
    tx = tce_node_registrator.registerTCENode(peer_id, {"from": alice})
    assert tx.events["NewTCENodeRegistered"].values() == [
        brownie.convert.datatypes.HexString(peer_id, "bytes")
    ]
