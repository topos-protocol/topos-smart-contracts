#!/usr/bin/env python3

import eth_abi
import logging as LOG
import re

from brownie import (
    accounts,
    convert,
    network,
    ConstAddressDeployer,
    ERC20Test,
    SubnetRegistrator,
    TCENodeRegistrator,
    TokenDeployer,
    ToposCoreContract,
    ToposCoreContractProxy,
)
from eth_abi.packed import encode_packed

# Contracts
def erc20_test(args):
    name = args[0]
    symbol = args[1]
    salt = args[2]

    # convert string input to bytes
    name_bytes = bytes(name, "utf-8")
    symbol_bytes = bytes(symbol, "utf-8")
    salt_bytes = bytes(salt, "utf-8")
    # encode constructor arguments
    contract_args = eth_abi.encode(
        ["bytes", "bytes"],
        [name_bytes, symbol_bytes],
    )
    # convert the bytecode from string to bytes
    bytecode_no_args = convert.to_bytes(ERC20Test.bytecode, "bytes")
    # encode the bytecode with constructor arguments
    bytecode = encode_packed(
        ["bytes", "bytes"], [bytecode_no_args, contract_args]
    )

    tx = const_address_deployer.deploy(
        bytecode,
        convert.to_bytes(salt_bytes, "bytes32"),
        {"from": accounts[0]},
    )
    LOG.info("address: " + tx.events["Deployed"]["deployedAddress"])


def subnet_registrator(args):
    salt = args[0]
    # convert string input to bytes
    salt_bytes = bytes(salt, "utf-8")
    # convert the bytecode from string to bytes
    bytecode_no_args = convert.to_bytes(SubnetRegistrator.bytecode, "bytes")
    tx = const_address_deployer.deploy(
        bytecode_no_args,
        convert.to_bytes(salt_bytes, "bytes32"),
        {"from": accounts[0]},
    )
    LOG.info("address: " + tx.events["Deployed"]["deployedAddress"])


def tce_node_registrator(args):
    salt = args[0]
    # convert string input to bytes
    salt_bytes = bytes(salt, "utf-8")
    # convert the bytecode from string to bytes
    bytecode_no_args = convert.to_bytes(TCENodeRegistrator.bytecode, "bytes")
    tx = const_address_deployer.deploy(
        bytecode_no_args,
        convert.to_bytes(salt_bytes, "bytes32"),
        {"from": accounts[0]},
    )
    LOG.info("address: " + tx.events["Deployed"]["deployedAddress"])


def token_deployer(args):
    salt = args[0]
    # convert string input to bytes
    salt_bytes = bytes(salt, "utf-8")
    # convert the bytecode from string to bytes
    bytecode_no_args = convert.to_bytes(TokenDeployer.bytecode, "bytes")
    tx = const_address_deployer.deploy(
        bytecode_no_args,
        convert.to_bytes(salt_bytes, "bytes32"),
        {"from": accounts[0]},
    )
    LOG.info("address: " + tx.events["Deployed"]["deployedAddress"])


def topos_core_contract(args):
    token_deployer_addr = args[0]
    subnet_id = args[1]
    salt = args[2]

    # convert string input to bytes
    subnet_id_bytes = bytes(subnet_id, "utf-8")
    salt_bytes = bytes(salt, "utf-8")
    # convert subnet_id bytes to bytes32
    subnet_id_bytes32 = convert.to_bytes(subnet_id_bytes, "bytes32")
    # encode constructor arguments
    contract_args = eth_abi.encode(
        ["address", "bytes32"],
        [token_deployer_addr, subnet_id_bytes32],
    )
    # convert the bytecode from string to bytes
    bytecode_no_args = convert.to_bytes(ToposCoreContract.bytecode, "bytes")
    # encode the bytecode with constructor arguments
    bytecode = encode_packed(
        ["bytes", "bytes"], [bytecode_no_args, contract_args]
    )

    tx = const_address_deployer.deploy(
        bytecode,
        convert.to_bytes(salt_bytes, "bytes32"),
        {"from": accounts[0]},
    )
    LOG.info("address: " + tx.events["Deployed"]["deployedAddress"])


def topos_core_contract_proxy(args):
    topos_core_contract_impl_addr = args[0]
    params = args[1]
    salt = args[2]

    # convert string input to bytes
    param_bytes = bytes(params, "utf-8")
    salt_bytes = bytes(salt, "utf-8")
    # encode constructor arguments
    contract_args = eth_abi.encode(
        ["address", "bytes"],
        [topos_core_contract_impl_addr, param_bytes],
    )
    # convert the bytecode from string to bytes
    bytecode_no_args = convert.to_bytes(
        ToposCoreContractProxy.bytecode, "bytes"
    )
    # encode the bytecode with constructor arguments
    bytecode = encode_packed(
        ["bytes", "bytes"], [bytecode_no_args, contract_args]
    )

    tx = const_address_deployer.deploy(
        bytecode,
        convert.to_bytes(salt_bytes, "bytes32"),
        {"from": accounts[0]},
    )


# Internal Functions
def camel_to_snake(name):
    name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", name).lower()


def init_const_addr_deployer(args):
    if len(args) < 1:
        raise Exception("Please provide ConstAddrDeployer address")
    global const_address_deployer
    const_address_deployer_addr = args[0]
    const_address_deployer = ConstAddressDeployer.at(
        const_address_deployer_addr
    )
    return args[1:]


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
        args = init_const_addr_deployer(args[2:])
        return args
    else:
        # for development just exclude the contract_name
        args = init_const_addr_deployer(args[1:])
        return args


def main(*args):
    if len(args) < 1:
        raise Exception("Please provide contract name")
    contract_name = args[0]
    deploy_args = init(*args)
    eval(camel_to_snake(contract_name))(deploy_args)


if __name__ == "__main__":
    main()
