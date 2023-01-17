import brownie

import const as c


def test_register_subnet_reverts_on_already_registered(
    alice, subnet_registrator
):
    register_subnet(alice, subnet_registrator)
    # should revert since subnet is already registered
    with brownie.reverts():
        register_subnet(alice, subnet_registrator)


def test_register_subnet_emits_event(alice, subnet_registrator):
    tx = register_subnet(alice, subnet_registrator)
    assert (
        subnet_registrator.subnetExists(c.SUBNET_PUBLIC_KEY, {"from": alice})
        is True
    )
    assert tx.events["NewSubnetRegistered"].values() == [
        brownie.convert.datatypes.HexString(c.SUBNET_PUBLIC_KEY, "bytes")
    ]


def test_remove_subnet_reverts_on_not_registered(alice, subnet_registrator):
    # should revert since subnet is not registered
    with brownie.reverts():
        subnet_registrator.removeSubnet(c.SUBNET_PUBLIC_KEY, {"from": alice})


def test_remove_subnet_emits_event(alice, subnet_registrator):
    register_subnet(alice, subnet_registrator)
    tx = subnet_registrator.removeSubnet(c.SUBNET_PUBLIC_KEY, {"from": alice})
    assert (
        subnet_registrator.subnetExists(c.SUBNET_PUBLIC_KEY, {"from": alice})
        is False
    )
    assert tx.events["SubnetRemoved"].values() == [
        brownie.convert.datatypes.HexString(c.SUBNET_PUBLIC_KEY, "bytes")
    ]


def test_get_subnet_count_returns_count(alice, subnet_registrator):
    subnet_count = 1
    register_subnet(alice, subnet_registrator)
    assert subnet_registrator.getSubnetCount({"from": alice}) == subnet_count


def test_get_subnet_id_at_index_returns_subnet_id(alice, subnet_registrator):
    index = 0  # only one registered subnet
    register_subnet(alice, subnet_registrator)
    assert (
        subnet_registrator.getSubnetIdAtIndex(index, {"from": alice})
        == c.SUBNET_BYTES
    )


# internal functions #
def register_subnet(alice, subnet_registrator):
    return subnet_registrator.registerSubnet(
        c.ENDPOINT,
        c.LOGO_URL,
        c.SUBNET_NAME,
        c.SUBNET_PUBLIC_KEY,
        c.SUBNET_CURRENCY_SYMBOL,
        {"from": alice},
    )
