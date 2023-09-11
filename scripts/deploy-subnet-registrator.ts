import { ContractFactory, providers, utils, Wallet } from 'ethers'
import subnetRegistratorJSON from '../artifacts/contracts/topos-core/SubnetRegistrator.sol/SubnetRegistrator.json'
import { Arg, deployContractConstant } from './const-addr-deployer'

const main = async function (..._args: Arg[]) {
  const [providerEndpoint, sequencerPrivateKey, salt, gasLimit, ...args] = _args
  const provider = new providers.JsonRpcProvider(<string>providerEndpoint)

  // Fetch the sequencer wallet
  const sequencerPrivateKeyHex = sanitizeHexString(
    <string>sequencerPrivateKey || ''
  )
  if (!utils.isHexString(sequencerPrivateKeyHex, 32)) {
    console.error('ERROR: Please provide a valid private key!')
    return
  }
  const sequencerWallet = new Wallet(sequencerPrivateKeyHex || '', provider)

  // Fetch the deployer wallet
  const privateKey = process.env.PRIVATE_KEY
  if (!privateKey || !utils.isHexString(privateKey, 32)) {
    console.error('ERROR: Please provide a valid private key! (PRIVATE_KEY)')
    return
  }
  const deployerWallet = new Wallet(process.env.PRIVATE_KEY || '', provider)

  // Deploy SubnetRegistrator contract with constant address
  let address
  try {
    address = (
      await deployContractConstant(
        deployerWallet,
        subnetRegistratorJSON,
        <string>salt,
        [...args],
        <number>gasLimit
      )
    ).address
  } catch (error) {
    console.error(error)
    return
  }
  console.log(address)

  // Initialize SubnetRegistrator contract
  const SubnetRegistratorFactory = new ContractFactory(
    subnetRegistratorJSON.abi,
    subnetRegistratorJSON.bytecode,
    deployerWallet
  )
  const subnetRegistrator = SubnetRegistratorFactory.attach(<string>address)
  subnetRegistrator.initialize(sequencerWallet.address)
}

const sanitizeHexString = function (hexString: string) {
  return hexString.startsWith('0x') ? hexString : `0x${hexString}`
}

const args = process.argv.slice(2)
main(...args)
