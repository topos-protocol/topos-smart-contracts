import brownie

import const as c


def test_register_tce_node_reverts_on_already_registered(
    alice, tce_node_registrator
):
    tce_node_registrator.registerTCENode(c.PEER_ID, {"from": alice})
    # should revert since tce node is already registered
    with brownie.reverts():
        tce_node_registrator.registerTCENode(c.PEER_ID, {"from": alice})


def test_register_tce_node_emits_event(alice, tce_node_registrator):
    tx = tce_node_registrator.registerTCENode(c.PEER_ID, {"from": alice})
    assert tx.events["NewTCENodeRegistered"].values() == [
        brownie.convert.datatypes.HexString(c.PEER_ID, "bytes")
    ]


def test_remove_tce_node_reverts_on_not_registered(
    alice, tce_node_registrator
):
    # should revert since tce node is not registered yet
    with brownie.reverts():
        tce_node_registrator.removeTCENode(c.PEER_ID, {"from": alice})


def test_remove_tce_node_emits_event(alice, tce_node_registrator):
    tce_node_registrator.registerTCENode(c.PEER_ID, {"from": alice})
    tx = tce_node_registrator.removeTCENode(c.PEER_ID, {"from": alice})
    tce_node = tce_node_registrator.tceNodes(c.PEER_ID)
    assert tce_node["isPresent"] is False
    assert tx.events["TCENodeRemoved"].values() == [
        brownie.convert.datatypes.HexString(c.PEER_ID, "bytes")
    ]
