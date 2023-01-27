<div id="top"></div>
<!-- PROJECT LOGO -->
<br />
<div align="center">

  <img src="./.github/assets/topos_logo.png#gh-light-mode-only" alt="Logo" width="200">
  <img src="./.github/assets/topos_logo_dark.png#gh-dark-mode-only" alt="Logo" width="200">

  <h3 align="center">Topos Smart Contracts</h3>

  <p align="center">
    Solidity smart contracts for Topos Protocol and Topos Messaging Protocol
  </p>
</div>

## Description

This repository contains Solidity smart contracts to be used with the Topos Protocol in the Topos ecosystem. The contract compilation/deployment and testing methods are taken care by the **Brownie** development framework.

## Installation

You need to install `pipx` in order to install Brownie into a virtual environment and make it available directly from the commandline.

To install `pipx`:

```
$ python3 -m pip install --user pipx
$ python3 -m pipx ensurepath
```

To install Brownie using `pipx`:

```
$ pipx install eth-brownie
```

Verify that Brownie is installed and working:

```
$ brownie
Brownie - Python development framework for Ethereum

Usage:  brownie <command> [<args>...] [options <args>]
```

## Other installation methods

To install via `pip`:

```
$ pip install eth-brownie
```

## Dependencies

This project contains some smart contracts which inherit from [OpenZeppelin contracts](https://github.com/OpenZeppelin/openzeppelin-contracts). This should be installed automatically via the Brownie Package Manager prior to compiling the project.

To install the dependency manually:

```
$ brownie pm install OpenZeppelin/openzeppelin-contracts@[VERSION]
```

The [VERSION] is needed to be specified.

## Compilation

To compile all of the contract sources within the `brownie/contracts/` subfolder:

```
$ npm run build
```

## Tests

Brownie utilizes the `pytest` framework for unit testing.

Note: run `npm install` to install `ganache` which is used by Brownie as a default local RPC client to launch.

To run the tests:

```
$ npm run test
```

## Linting

For formatting this project uses `prettier` with the `prettier-plugin-solidity` plugin. For general style guide and security checks this project uses `Solhint`.

For linting the Python test files this project uses `Flake8` to check for any style, syntax, naming and complexity issues. This project also uses `Black` for formatting the Python tests.

To install the packages:

```
$ npm install
```

To run linter:

```
$ npm run lint
```

To fix the format:

```
$ npm run lint:fix
```

## Deployment

To deploy contracts with `DEPLOY2`, refer to the [next section](#deployment-with-deploy2).

Add an account to Brownie accounts and assign an `id` to it:

```
$ brownie accounts generate <id> # generate a new account

$ brownie accounts new <id> # add an already existing account

$ brownie accounts import <id> <path> # import an account from a JSON keystore file
```

Example:

```
$ brownie accounts new substrate_alice
Brownie v1.19.2 - Python development framework for Ethereum

Enter the private key you wish to add: 0x99B3C12287537E38C90A9219D4CB074A89A16E9CDB20BF85728EBD97C343E342
Enter the password to encrypt this account with:
SUCCESS: A new account '0x6Be02d1d3665660d22FF9624b7BE0551ee1Ac91b' has been generated with the id 'substrate_alice'
```

In order to deploy the smart contracts, run the basic deployment script:

```
$ npm run deploy <contract_name> <id> <arg1> <arg2> -- --network <network_name>
```

Example:

```
$ npm run deploy ToposCore substrate_alice 0x4897d0802e611AF187db47C7648e8B0Ef759e3aa 1 -- --network topos_subnet
```

There is no need to specify the `id` or the `network_name` for the `development` network

Example:

```
$ npm run deploy ToposCore 0x4897d0802e611AF187db47C7648e8B0Ef759e3aa 1
```

## Deployment of a single contract with CREATE2

A NodeJS script is made available to deploy contracts with `CREATE2`, i.e., with constant addresses. The script is to be used with a deployed instance of `ConstAddressDeployer`. See an example below:

```
npm run deploy2 http://myChainRPCEndpoint myCompiledContract.json MySecretSalt ACustomGasLimit|null MyConstructorArg AnotherConstructorArg
# npm run deploy2 http://127.0.0.1:8545 brownie/build/contracts/ToposCore.json $TOPOS_CORE_SALT 2000000 0xF121424e3F7d73fCD79DcBCA67E8F10BeBE67b00 0x3100000000000000000000000000000000000000000000000000000000000000
```

## Deployment of the full Topos Messaging Protocol

To deploy the full Topos Messaging Protocol, another `deploy2:topos-msg-protocol` npm script is available. This scripts deploys the following contracts:

- `TokenDeployer` with constant address
- `ToposCore`
- `ToposCoreProxy` with constant address

```
npm run deploy2:topos-msg-protocol http://myChainRPCEndpoint
# npm run deploy2:topos-msg-protocol http://127.0.0.1:8545
```

## Docker

Some of the above commands can be run in docker.

```
$ docker build . --t target [build|test|lint]
```

## License

This project is released under the terms of the MIT license.
