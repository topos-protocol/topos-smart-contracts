import {
  Contract,
  ContractFactory,
  utils,
  Wallet,
  ContractInterface,
  BigNumber,
  ContractTransaction,
} from 'ethers'

import ConstAddressDeployerJSON from '../artifacts/contracts/topos-core/ConstAddressDeployer.sol/ConstAddressDeployer.json'

export type ContractOutputJSON = { abi: ContractInterface; bytecode: string }

const CONST_ADDRESS_DEPLOYER_ADDR = '0x0000000000000000000000000000000000001110'

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
  const deployer = new Contract(
    CONST_ADDRESS_DEPLOYER_ADDR,
    ConstAddressDeployerJSON.abi,
    wallet
  )

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
  const deployer = new Contract(
    CONST_ADDRESS_DEPLOYER_ADDR,
    ConstAddressDeployerJSON.abi,
    wallet
  )

  const salt = getSaltFromKey('')
  const factory = new ContractFactory(contractJson.abi, contractJson.bytecode)
  const bytecode = factory.getDeployTransaction(...args).data

  const address = await deployer.deployedAddress(bytecode, wallet.address, salt)
  const contract = new Contract(address, contractJson.abi, wallet)
  const initData = (await contract.populateTransaction.init(...initArgs)).data

  return deployer.estimateGas.deployAndInit(bytecode, salt, initData)
}

export const deployContractConstant = async (
  wallet: Wallet,
  contractJson: ContractOutputJSON,
  key: string,
  args: any[] = [],
  gasLimit: number | null = null
) => {
  const deployer = new Contract(
    CONST_ADDRESS_DEPLOYER_ADDR,
    ConstAddressDeployerJSON.abi,
    wallet
  )
  const salt = getSaltFromKey(key)

  const factory = new ContractFactory(contractJson.abi, contractJson.bytecode)

  const bytecode = factory.getDeployTransaction(...args).data

  const gas = gasLimit
    ? BigNumber.from(gasLimit)
    : await estimateGasForDeploy(wallet, contractJson, args)

  const tx: ContractTransaction = await deployer
    .connect(wallet)
    .deploy(bytecode, salt, {
      gasLimit: BigInt(Math.floor(gas.toNumber() * 1.2)),
    })

  await tx.wait()

  const address = await deployer.deployedAddress(bytecode, wallet.address, salt)

  return new Contract(address, contractJson.abi, wallet)
}

export const deployAndInitContractConstant = async (
  wallet: Wallet,
  contractJson: ContractOutputJSON,
  key: string,
  args: any[] = [],
  initArgs: any[] = [],
  gasLimit: number | null = null
) => {
  const deployer = new Contract(
    CONST_ADDRESS_DEPLOYER_ADDR,
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
  wallet: Wallet,
  contractJson: ContractOutputJSON,
  key: string,
  args: any[] = []
) => {
  const deployer = new Contract(
    CONST_ADDRESS_DEPLOYER_ADDR,
    ConstAddressDeployerJSON.abi,
    wallet
  )
  const salt = getSaltFromKey(key)

  const factory = new ContractFactory(contractJson.abi, contractJson.bytecode)
  const bytecode = factory.getDeployTransaction(...args).data
  return await deployer.deployedAddress(bytecode, wallet.address, salt)
}
