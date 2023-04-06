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

This repository contains Solidity smart contracts to be used with the Topos Protocol in the Topos ecosystem. The contract compilation/deployment and testing methods are taken care by the **Hardhat** development framework.

## Installation

To install the project along with all the dependencies run:

```
$ npm install
```

## Dependencies

This project contains some smart contracts which inherit from [OpenZeppelin contracts](https://github.com/OpenZeppelin/openzeppelin-contracts). This should be installed automatically.

## Compilation

To compile run:

```
$ npm run compile
```

## Tests

To run the tests:

```
$ npm run test
```

## Coverage

To see the test coverage run:

```
npm run coverage
```

## Linting

For formatting this project uses `prettier` with the `prettier-plugin-solidity` plugin. For general style guide and security checks this project uses `Solhint`.

To run linter:

```
$ npm run lint
```

To fix the format:

```
$ npm run lint:fix
```

To run Slither:
  
  ```
  $ npm run slither
  ```

## Deployment

### Deployment of a single contract with CREATE2

A NodeJS script is made available to deploy contracts with `CREATE2`, i.e., with constant addresses. The script is to be used with a deployed instance of `ConstAddressDeployer`. See an example below:

```
npm run deploy2 http://myChainRPCEndpoint myCompiledContract.json MySecretSalt ACustomGasLimit|null MyConstructorArg AnotherConstructorArg
# npm run deploy2 http://127.0.0.1:8545 artifacts/contracts/topos-core/ToposCore.sol/ToposCore.json $TOPOS_CORE_SALT 2000000 0xF121424e3F7d73fCD79DcBCA67E8F10BeBE67b00 0x3100000000000000000000000000000000000000000000000000000000000000
```

### Deployment of the full Topos Messaging Protocol

To deploy the full Topos Messaging Protocol, another `deploy2:topos-msg-protocol` npm script is available. This scripts deploys the following contracts:

- `TokenDeployer` with constant address
- `ToposCore` with constant address
- `ToposCoreProxy` with constant address

```
npm run deploy2:topos-msg-protocol http://myChainRPCEndpoint pathToSequencerPrivateKey
# npm run deploy2:topos-msg-protocol http://127.0.0.1:8545 /data/node-1/consensus/validator.key
```

## Docker

Some of the above commands can be run in docker.

```
$ docker build . --t target [build|test|lint]
```

## License

This project is released under the terms of the MIT license.
