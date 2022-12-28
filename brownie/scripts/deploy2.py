#!/usr/bin/env python3

import logging as LOG
import re

from brownie import (
    accounts,
    network,
    ConstAddressDeployer,
    ERC20Test,
    SubnetRegistrator,
    TCENodeRegistrator,
    TokenDeployer,
    ToposCoreContract,
)

def main(*args):
    bytecode = args[0]
    salt = args[1]
    const_address_deployer=ConstAddressDeployer.at("0x01110")
    const_address_deployer.deploy(bytecode, salt)


if __name__ == "__main__":
    main()
