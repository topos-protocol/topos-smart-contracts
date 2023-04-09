import {
  Contract,
  ContractFactory,
  utils,
  Wallet,
  ContractInterface,
  BigNumber,
} from 'ethers'

import ConstAddressDeployerJSON from '../artifacts/contracts/topos-core/ConstAddressDeployer.sol/ConstAddressDeployer.json'

export type ContractOutputJSON = { abi: ContractInterface; bytecode: string }

const getSaltFromKey = (key: string) => {
  return utils.keccak256(
    utils.defaultAbiCoder.encode(['string'], [key.toString()])
  )
}

export const estimateGasForDeploy = async (
  wallet: Wallet,
  contractJson: ContractOutputJSON,
  args: any[] = []
) => {
  const deployerFactory = new ContractFactory(
    ConstAddressDeployerJSON.abi,
    ConstAddressDeployerJSON.bytecode,
    wallet
  )

  const deployer = await deployerFactory.deploy()
  await deployer.deployed()

  const salt = getSaltFromKey('')
  const factory = new ContractFactory(contractJson.abi, contractJson.bytecode)
  const bytecode = factory.getDeployTransaction(...args).data
  return await deployer.estimateGas.deploy(bytecode, salt)
}

export const estimateGasForDeployAndInit = async (
  wallet: Wallet,
  contractJson: ContractOutputJSON,
  args: any[] = [],
  initArgs: any[] = []
) => {
  const deployerFactory = new ContractFactory(
    ConstAddressDeployerJSON.abi,
    ConstAddressDeployerJSON.bytecode,
    wallet
  )

  const deployer = await deployerFactory.deploy()
  await deployer.deployed()

  const salt = getSaltFromKey('')
  const factory = new ContractFactory(contractJson.abi, contractJson.bytecode)
  const bytecode = factory.getDeployTransaction(...args).data

  const address = await deployer.deployedAddress(bytecode, wallet.address, salt)
  const contract = new Contract(address, contractJson.abi, wallet)
  const initData = (await contract.populateTransaction.init(...initArgs)).data

  return deployer.estimateGas.deployAndInit(bytecode, salt, initData)
}

export const deployContractConstant = async (
  deployerAddress: string,
  wallet: Wallet,
  contractJson: ContractOutputJSON,
  key: string,
  args: any[] = [],
  gasLimit: number | null = null
) => {
  const deployer = new Contract(
    deployerAddress,
    ConstAddressDeployerJSON.abi,
    wallet
  )
  const salt = getSaltFromKey(key)
  const factory = new ContractFactory(contractJson.abi, contractJson.bytecode)
  const bytecode = factory.getDeployTransaction(...args).data
  const gas =
    gasLimit !== null
      ? BigNumber.from(gasLimit) ||
        (await estimateGasForDeploy(wallet, contractJson, args))
      : null
  const tx = await deployer.connect(wallet).deploy(
    bytecode,
    salt,
    gas
      ? {
          gasLimit: BigInt(Math.floor(gas.toNumber() * 1.2)),
        }
      : {}
  )
  await tx.wait()
  const address = await deployer.deployedAddress(bytecode, wallet.address, salt)
  return new Contract(address, contractJson.abi, wallet)
}

export const deployAndInitContractConstant = async (
  deployerAddress: string,
  wallet: Wallet,
  contractJson: ContractOutputJSON,
  key: string,
  args: any[] = [],
  initArgs: any[] = [],
  gasLimit: number | null = null
) => {
  const deployer = new Contract(
    deployerAddress,
    ConstAddressDeployerJSON.abi,
    wallet
  )
  const salt = getSaltFromKey(key)
  const factory = new ContractFactory(contractJson.abi, contractJson.bytecode)
  const bytecode = factory.getDeployTransaction(...args).data
  const address = await deployer.deployedAddress(bytecode, wallet.address, salt)
  const contract = new Contract(address, contractJson.abi, wallet)
  const initData = (await contract.populateTransaction.init(...initArgs)).data
  const tx = await deployer
    .connect(wallet)
    .deployAndInit(bytecode, salt, initData, {
      gasLimit,
    })
  await tx.wait()
  return contract
}

export const predictContractConstant = async (
  deployerAddress: string,
  wallet: Wallet,
  contractJson: ContractOutputJSON,
  key: string,
  args: any[] = []
) => {
  const deployer = new Contract(
    deployerAddress,
    ConstAddressDeployerJSON.abi,
    wallet
  )
  const salt = getSaltFromKey(key)

  const factory = new ContractFactory(contractJson.abi, contractJson.bytecode)
  const bytecode = factory.getDeployTransaction(...args).data
  return await deployer.deployedAddress(bytecode, wallet.address, salt)
}
