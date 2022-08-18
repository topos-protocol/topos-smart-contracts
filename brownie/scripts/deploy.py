from brownie import Asset, ToposCoreContract, accounts


def main():

    asset = Asset.deploy("Test Token", "TST", 1e23, {'from': accounts[0]})
    topos_core_contract = ToposCoreContract.deploy(1, {'from': accounts[0]})
    return asset, topos_core_contract
