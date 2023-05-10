import {
  Contract,
  ContractFactory,
  ContractTransaction,
  providers,
  utils,
  Wallet,
} from 'ethers'

import tokenDeployerJSON from '../artifacts/contracts/topos-core/TokenDeployer.sol/TokenDeployer.json'
import toposCoreJSON from '../artifacts/contracts/topos-core/ToposCore.sol/ToposCore.json'
import toposCoreProxyJSON from '../artifacts/contracts/topos-core/ToposCoreProxy.sol/ToposCoreProxy.json'
import toposCoreInterfaceJSON from '../artifacts/contracts/interfaces/IToposCore.sol/IToposCore.json'
import toposMessagingJSON from '../artifacts/contracts/topos-core/ToposMessaging.sol/ToposMessaging.json'

const main = async function (...args: string[]) {
  const [providerEndpoint, _sequencerPrivateKey] = args
  const provider = providers.getDefaultProvider(providerEndpoint)
  const toposDeployerPrivateKey = sanitizeHexString(
    process.env.PRIVATE_KEY || ''
  )

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

  const wallet = new Wallet(toposDeployerPrivateKey, provider)

  // Deploy ConstAddressDeployer
  const TokenDeployerFactory = new ContractFactory(
    tokenDeployerJSON.abi,
    tokenDeployerJSON.bytecode,
    wallet
  )
  const TokenDeployer = await TokenDeployerFactory.deploy({
    gasLimit: 5_000_000,
  })
  await TokenDeployer.deployed()
  console.log(`Token Deployer deployed to ${TokenDeployer.address}`)

  // Deploy ToposCore
  const ToposCoreFactory = new ContractFactory(
    toposCoreJSON.abi,
    toposCoreJSON.bytecode,
    wallet
  )
  const ToposCore = await ToposCoreFactory.deploy({
    gasLimit: 5_000_000,
  })
  await ToposCore.deployed()
  console.log(`Topos Core contract deployed to ${ToposCore.address}`)

  // Deploy ToposCoreProxy
  const toposCoreProxyParams = utils.defaultAbiCoder.encode(
    ['address[]', 'uint256'],
    [[wallet.address], 1] // TODO: Use a different admin address than ToposDeployer
  )
  const ToposCoreProxyFactory = new ContractFactory(
    toposCoreProxyJSON.abi,
    toposCoreProxyJSON.bytecode,
    wallet
  )
  const ToposCoreProxy = await ToposCoreProxyFactory.deploy(
    ToposCore.address,
    toposCoreProxyParams,
    { gasLimit: 5_000_000 }
  )
  await ToposCoreProxy.deployed()
  console.log(`Topos Core Proxy contract deployed to ${ToposCoreProxy.address}`)

  // Deploy ToposMessaging
  const ToposMessagingFactory = new ContractFactory(
    toposMessagingJSON.abi,
    toposMessagingJSON.bytecode,
    wallet
  )
  const ToposMessaging = await ToposMessagingFactory.deploy(
    TokenDeployer.address,
    ToposCoreProxy.address,
    { gasLimit: 5_000_000 }
  )
  await ToposMessaging.deployed()
  console.log(`Topos Messaging contract deployed to ${ToposMessaging.address}`)

  console.info(`\nSetting subnetId on ToposCore via proxy`)
  const toposCoreInterface = new Contract(
    ToposCoreProxy.address,
    toposCoreInterfaceJSON.abi,
    wallet
  )
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

  console.info(`\nReading subnet id`)
  const networkSubnetId = await toposCoreInterface.networkSubnetId()

  console.info(
    `Successfully set ${networkSubnetId} subnetId on ToposCore via proxy\n`
  )
}

const sanitizeHexString = function (hexString: string) {
  return hexString.startsWith('0x') ? hexString : `0x${hexString}`
}

const args = process.argv.slice(2)
main(...args)
