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
    subnet = subnet_registrator.subnets(c.SUBNET_PUBLIC_KEY)
    assert subnet["isPresent"] is False
    assert tx.events["SubnetRemoved"].values() == [
        brownie.convert.datatypes.HexString(c.SUBNET_PUBLIC_KEY, "bytes")
    ]


# internal functions #
def register_subnet(alice, subnet_registrator):
    return subnet_registrator.registerSubnet(
        c.ENDPOINT,
        c.LOGO_URL,
        c.SUBNET_NAME,
        c.SUBNET_PUBLIC_KEY,
        {"from": alice},
    )
