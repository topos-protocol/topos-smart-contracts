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


# Contracts
def const_address_deployer(_):
    ConstAddressDeployer.deploy({"from": accounts[0]})


def erc20_test(args):
    name = args[0]
    symbol = args[1]
    ERC20Test.deploy(name, symbol, {"from": accounts[0]})


def subnet_registrator(_):
    SubnetRegistrator.deploy({"from": accounts[0]})


def tce_node_registrator(_):
    TCENodeRegistrator.deploy({"from": accounts[0]})


def token_deployer(_):
    TokenDeployer.deploy({"from": accounts[0]})


def topos_core_contract(args):
    token_deployer_addr = args[0]
    subnet_id = args[1]
    ToposCoreContract.deploy(
        token_deployer_addr, subnet_id, {"from": accounts[0]}
    )


# Internal Functions
def camel_to_snake(name):
    name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", name).lower()


def init(*args):
    LOG.basicConfig(
        format="%(asctime)s [%(levelname)s]"
        + "%(message)s (%(filename)s:%(lineno)s)",
        datefmt="%Y-%m-%d %H:%M:%S",
        level=LOG.INFO,
    )
    active_network = network.show_active()
    LOG.info("Connected to: " + active_network)
    # for other networks an account is required
    if active_network != "development":
        if len(args) < 2:
            raise Exception("Please provide a local account")
        account = args[1]
        accounts.load(account)
        # exclude the contract_name and the account
        return args[2:]
    else:
        # for development just exclude the contract_name
        return args[1:]


def main(*args):
    if len(args) < 1:
        raise Exception("Please provide contract name")
    contract_name = args[0]
    deploy_args = init(*args)
    eval(camel_to_snake(contract_name))(deploy_args)


if __name__ == "__main__":
    main()
