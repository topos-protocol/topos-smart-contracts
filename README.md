
<div id="top"></div>
<!-- PROJECT LOGO -->
<br />
<div align="center">

  <img src="./.github/assets/logo.png#gh-light-mode-only" alt="Logo" width="300">
  <img src="./.github/assets/logo_dark.png#gh-dark-mode-only" alt="Logo" width="300">

  <h3 align="center">Topos Smart Contracts</h3>

  <p align="center">
    Solidity smart contracts for Cross-Subnet Protocol
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

This project contains some smart contracts which inherit from  [OpenZeppelin contracts](https://github.com/OpenZeppelin/openzeppelin-contracts). This should be installed automatically via the Brownie Package Manager prior to compiling the project.

To install the dependency manually:
```
$ brownie pm install OpenZeppelin/openzeppelin-contracts@[VERSION]
```
The [VERSION] is needed to be specified.

## Compilation

To compile all of the contract sources within the `brownie/contracts/` subfolder:
```
$ brownie compile
```

## Tests

Brownie utilizes the `pytest` framework for unit testing.

Note: run `yarn install` to install `ganache` which is used by Brownie as a default local RPC client to launch.

To run the tests:
```
$ yarn test
```

## Linting
For ease of linting a configuration file `package.json` is provided. It contains the necessary dependencies and scripts to run the linting tools.

For formatting this project uses `prettier` with the `prettier-plugin-solidity` plugin. For general style guide and security checks this project uses `Solhint`.

For linting the Python test files this project uses `Flake8` to check for any style, syntax, naming and complexity issues. This project also uses `Black` for formatting the Python tests.

To install the packages:
```
$ yarn install
```

To run linter:
```
$ yarn lint
```

To fix the format:
```
$ yarn lint:fix
```

## Deployment

In order to deploy the smart contracts run the basic deployment script:

```
$ brownie run deploy
```

## License

This project is released under the terms of the MIT license.
