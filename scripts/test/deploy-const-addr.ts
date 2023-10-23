import { ContractFactory, Wallet, providers } from 'ethers'

import ConstAddressDeployerJSON from '../../artifacts/contracts/topos-core/ConstAddressDeployer.sol/ConstAddressDeployer.json'

/// function to deploy the constant address deployer
const main = async function (...args: string[]) {
  const [providerEndpoint, privateKey] = args
  const provider = new providers.JsonRpcProvider(providerEndpoint)
  const toposDeployerPrivateKey = sanitizeHexString(privateKey || '')

  // deploy the constant address deployer
  const wallet = new Wallet(toposDeployerPrivateKey, provider)
  const ConstAddressDeployerFactory = new ContractFactory(
    ConstAddressDeployerJSON.abi,
    ConstAddressDeployerJSON.bytecode,
    wallet
  )
  const ConstAddressDeployer = await ConstAddressDeployerFactory.deploy({
    gasLimit: 5_000_000,
  })
  await ConstAddressDeployer.deployed()
  console.log('ConstAddressDeployer deployed to:', ConstAddressDeployer.address)
}

const sanitizeHexString = function (hexString: string) {
  return hexString.startsWith('0x') ? hexString : `0x${hexString}`
}

const args = process.argv.slice(2)
main(...args)
