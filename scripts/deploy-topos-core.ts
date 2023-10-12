import {
  Contract,
  ContractFactory,
  ContractTransaction,
  BigNumber,
  Wallet,
  providers,
  utils,
} from 'ethers'

import toposCoreJSON from '../artifacts/contracts/topos-core/ToposCore.sol/ToposCore.json'
import toposCoreProxyJSON from '../artifacts/contracts/topos-core/ToposCoreProxy.sol/ToposCoreProxy.json'
import toposCoreInterfaceJSON from '../artifacts/contracts/interfaces/IToposCore.sol/IToposCore.json'

const main = async function (...args: string[]) {
  const [_providerEndpoint, _sequencerPrivateKey, _gasLimit] = args
  const provider = new providers.JsonRpcProvider(_providerEndpoint)

  const toposDeployerPrivateKey = sanitizeHexString(
    process.env.PRIVATE_KEY || ''
  )
  if (!utils.isHexString(toposDeployerPrivateKey, 32)) {
    console.error(
      'ERROR: Please provide a valid toposDeployer private key! (PRIVATE_KEY)'
    )
    process.exit(1)
  }

  const sequencerPrivateKey = sanitizeHexString(_sequencerPrivateKey || '')
  if (!utils.isHexString(sequencerPrivateKey, 32)) {
    console.error('ERROR: Please provide a valid sequencer private key!')
    process.exit(1)
  }

  const toposDeployerWallet = new Wallet(toposDeployerPrivateKey, provider)
  const ToposCoreFactory = new ContractFactory(
    toposCoreJSON.abi,
    toposCoreJSON.bytecode,
    toposDeployerWallet
  )
  const toposCore = await ToposCoreFactory.deploy({
    gasLimit: _gasLimit ? BigNumber.from(_gasLimit) : 5_000_000,
  })
  await toposCore.deployed()

  const ToposCoreProxyFactory = new ContractFactory(
    toposCoreProxyJSON.abi,
    toposCoreProxyJSON.bytecode,
    toposDeployerWallet
  )
  const toposCoreProxy = await ToposCoreProxyFactory.deploy(toposCore.address, {
    gasLimit: _gasLimit ? BigNumber.from(_gasLimit) : 5_000_000,
  })
  await toposCoreProxy.deployed()

  const sequencerWallet = new Wallet(sequencerPrivateKey, provider)
  const toposCoreInterface = new Contract(
    toposCoreProxy.address,
    toposCoreInterfaceJSON.abi,
    sequencerWallet
  )
  const adminThreshold = 1
  await initialize(toposCoreInterface, sequencerWallet, adminThreshold)

  const isCompressed = true
  const sequencerPublicKey = utils.computePublicKey(
    sequencerPrivateKey,
    isCompressed
  )
  const subnetId = sanitizeHexString(sequencerPublicKey.substring(4))
  await setSubnetId(toposCoreInterface, subnetId)

  console.log(`
export TOPOS_CORE_CONTRACT_ADDRESS=${toposCore.address}
export TOPOS_CORE_PROXY_CONTRACT_ADDRESS=${toposCoreProxy.address}
  `)
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

const sanitizeHexString = function (hexString: string) {
  return hexString.startsWith('0x') ? hexString : `0x${hexString}`
}

const args = process.argv.slice(2)
main(...args)
