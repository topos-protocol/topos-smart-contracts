import brownie

endpoint = brownie.convert.to_bytes("0xdead", "bytes")
logo_url = brownie.convert.to_bytes("0xdeed", "bytes")
name = "Test Subnet"
public_key = brownie.convert.to_bytes("0xdeaf", "bytes")


def test_register_subnet_reverts_on_already_registered(
    alice, subnet_registrator
):
    subnet_registrator.registerSubnet(
        endpoint, logo_url, name, public_key, {"from": alice}
    )
    # should revert since subnet is already registered
    with brownie.reverts():
        subnet_registrator.registerSubnet(
            endpoint, logo_url, name, public_key, {"from": alice}
        )


def test_register_subnet_emits_event(alice, subnet_registrator):
    tx = subnet_registrator.registerSubnet(
        endpoint, logo_url, name, public_key, {"from": alice}
    )
    assert tx.events["NewSubnetRegistered"].values() == [
        brownie.convert.datatypes.HexString(public_key, "bytes")
    ]
