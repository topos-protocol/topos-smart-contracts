import { providers, utils, Wallet } from 'ethers'
import subnetRegistratorJSON from '../artifacts/contracts/topos-core/SubnetRegistrator.sol/SubnetRegistrator.json'
import { Arg, deployContractConstant } from './const-addr-deployer'

const main = async function (..._args: Arg[]) {
  const [providerEndpoint, privateKey, salt, gasLimit, ...args] = _args
  const provider = new providers.JsonRpcProvider(<string>providerEndpoint)

  const sequencerPrivateKey = sanitizeHexString(<string>privateKey || '')
  if (!utils.isHexString(sequencerPrivateKey, 32)) {
    console.error('ERROR: Please provide a valid private key!')
    return
  }

  const wallet = new Wallet(sequencerPrivateKey || '', provider)
  const address = await deployContractConstant(
    wallet,
    subnetRegistratorJSON,
    <string>salt,
    [wallet.address, ...args],
    <number>gasLimit
  )
    .then(({ address }) => address)
    .catch(console.error)
  console.log(address)
}

const sanitizeHexString = function (hexString: string) {
  return hexString.startsWith('0x') ? hexString : `0x${hexString}`
}

const args = process.argv.slice(2)
main(...args)
