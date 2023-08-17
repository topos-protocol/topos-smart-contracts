import { Contract, ContractTransaction, providers, utils, Wallet } from 'ethers'

import tokenDeployerJSON from '../artifacts/contracts/topos-core/TokenDeployer.sol/TokenDeployer.json'
import toposCoreJSON from '../artifacts/contracts/topos-core/ToposCore.sol/ToposCore.json'
import toposCoreProxyJSON from '../artifacts/contracts/topos-core/ToposCoreProxy.sol/ToposCoreProxy.json'
import toposCoreInterfaceJSON from '../artifacts/contracts/interfaces/IToposCore.sol/IToposCore.json'
import erc20MessagingJSON from '../artifacts/contracts/examples/ERC20Messaging.sol/ERC20Messaging.json'
import {
  Arg,
  ContractOutputJSON,
  deployContractConstant,
  predictContractConstant,
} from './const-addr-deployer'

const main = async function (...args: string[]) {
  const [providerEndpoint, _sequencerPrivateKey] = args
  const provider = new providers.JsonRpcProvider(providerEndpoint)
  const toposDeployerPrivateKey = sanitizeHexString(
    process.env.PRIVATE_KEY || ''
  )
  const tokenDeployerSalt = process.env.TOKEN_DEPLOYER_SALT
  const toposCoreSalt = process.env.TOPOS_CORE_SALT
  const toposCoreProxySalt = process.env.TOPOS_CORE_PROXY_SALT
  const erc20MessagingSalt = process.env.ERC20_MESSAGING_SALT

  if (!_sequencerPrivateKey) {
    console.error('ERROR: Please provide the sequencer private key!')
    process.exit(1)
  }

  const sequencerPrivateKey = sanitizeHexString(_sequencerPrivateKey)

  if (!utils.isHexString(sequencerPrivateKey, 32)) {
    console.error('ERROR: The sequencer private key is not a valid key!')
    process.exit(1)
  }

  const isCompressed = true
  const sequencerPublicKey = utils.computePublicKey(
    sequencerPrivateKey,
    isCompressed
  )

  const subnetId = sanitizeHexString(sequencerPublicKey.substring(4))

  if (!utils.isHexString(toposDeployerPrivateKey, 32)) {
    console.error(
      'ERROR: Please provide a valid toposDeployer private key! (PRIVATE_KEY)'
    )
    process.exit(1)
  }

  verifySalt('TokenDeployer', 'TOKEN_DEPLOYER_SALT', tokenDeployerSalt)
  verifySalt('ToposCore', 'TOPOS_CORE_SALT', toposCoreSalt)
  verifySalt('ToposCoreProxy', 'TOPOS_CORE_PROXY_SALT', toposCoreProxySalt)
  verifySalt('ERC20Messaging', 'ERC20_MESSAGING_SALT', erc20MessagingSalt)

  const wallet = new Wallet(toposDeployerPrivateKey, provider)

  const tokenDeployerAddress = await processContract(
    wallet,
    tokenDeployerJSON,
    tokenDeployerSalt!,
    [],
    8_000_000
  )

  const toposCoreAddress = await processContract(
    wallet,
    toposCoreJSON,
    toposCoreSalt!,
    [],
    4_000_000
  )

  const toposCoreProxyAddress = await processContract(
    wallet,
    toposCoreProxyJSON,
    toposCoreProxySalt!,
    [toposCoreAddress],
    4_000_000
  )

  const sequencerWallet = new Wallet(sequencerPrivateKey, provider)
  const toposCoreInterface = new Contract(
    toposCoreProxyAddress,
    toposCoreInterfaceJSON.abi,
    sequencerWallet
  )
  const adminThreshold = 1
  await initialize(toposCoreInterface, sequencerWallet, adminThreshold)

  const erc20MessagingAddresss = await processContract(
    wallet,
    erc20MessagingJSON,
    erc20MessagingSalt!,
    [tokenDeployerAddress, toposCoreProxyAddress],
    4_000_000
  )

  setSubnetId(toposCoreInterface, subnetId)

  console.log(`
export TOPOS_CORE_CONTRACT_ADDRESS=${toposCoreAddress}
export TOPOS_CORE_PROXY_CONTRACT_ADDRESS=${toposCoreProxyAddress}
export TOKEN_DEPLOYER_CONTRACT_ADDRESS=${tokenDeployerAddress}
export ERC20_MESSAGING_CONTRACT_ADDRESS=${erc20MessagingAddresss}
  `)
}

const sanitizeHexString = function (hexString: string) {
  return hexString.startsWith('0x') ? hexString : `0x${hexString}`
}

const verifySalt = function (
  contractName: string,
  envVarName: string,
  localVar: string | undefined
) {
  if (!localVar) {
    console.error(
      `ERROR: Please provide a salt for ${contractName}! (${envVarName})`
    )
    process.exit(1)
  }
}

const processContract = async function (
  wallet: Wallet,
  contractJson: ContractOutputJSON,
  salt: string,
  args: Arg[] = [],
  gasLimit: number | null = null
) {
  const predictedContractAddress = await predictContractConstant(
    wallet,
    contractJson,
    salt,
    args
  ).catch((error) => {
    console.error(error)
    process.exit(1)
  })

  const codeAtPredictedAddress = await wallet.provider.getCode(
    predictedContractAddress
  )

  const thereIsCodeAtAddress = codeAtPredictedAddress !== '0x'

  if (thereIsCodeAtAddress) {
    return predictedContractAddress
  } else {
    const newContractAddress = await deployContractConstant(
      wallet,
      contractJson,
      salt,
      args,
      gasLimit
    )
      .then((contract) => contract.address)
      .catch((error) => {
        console.error(error)
        process.exit(1)
      })

    return newContractAddress
  }
}

const setSubnetId = async function (
  toposCoreInterface: Contract,
  subnetId: string
) {
  await toposCoreInterface
    .setNetworkSubnetId(subnetId, { gasLimit: 4_000_000 })
    .then(async (tx: ContractTransaction) => {
      await tx.wait().catch((error) => {
        console.error(
          `Error: Failed (wait) to set ${subnetId} subnetId on ToposCore via proxy!`
        )
        console.error(error)
        process.exit(1)
      })
    })
    .catch((error: Error) => {
      console.error(
        `Error: Failed to set ${subnetId} subnetId on ToposCore via proxy!`
      )
      console.error(error)
      process.exit(1)
    })

  await toposCoreInterface.networkSubnetId()
}

async function initialize(
  toposCoreInterface: Contract,
  wallet: Wallet,
  adminThreshold: number
) {
  await toposCoreInterface
    .initialize([wallet.address], adminThreshold, { gasLimit: 4_000_000 })
    .then(async (tx: ContractTransaction) => {
      await tx.wait().catch((error) => {
        console.error(`Error: Failed (wait) to initialize ToposCore via proxy!`)
        console.error(error)
        process.exit(1)
      })
    })
    .catch((error: Error) => {
      console.error(`Error: Failed to initialize ToposCore via proxy!`)
      console.error(error)
      process.exit(1)
    })
}

const args = process.argv.slice(2)
main(...args)
