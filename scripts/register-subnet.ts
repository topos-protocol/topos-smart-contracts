import { Contract, ContractTransaction, providers, utils, Wallet } from 'ethers'

import subnetRegistratorJSON from '../artifacts/contracts/topos-core/SubnetRegistrator.sol/SubnetRegistrator.json'

const main = async function (...args: string[]) {
  const [
    toposSubnetProviderEndpoint,
    subnetRegistratorAddress,
    subnetName,
    subnetChainId,
    subnetRPCEndpoint,
    subnetCurrencySymbol,
    subnetLogoUrl,
    _sequencerPrivateKey,
  ] = args
  const provider = new providers.JsonRpcProvider(toposSubnetProviderEndpoint)
  const toposDeployerPrivateKey = sanitizeHexString(
    process.env.PRIVATE_KEY || ''
  )

  if (!_sequencerPrivateKey) {
    console.error('ERROR: Please provide the sequencer private key!')
    process.exit(1)
  }

  if (!subnetRPCEndpoint) {
    console.error('ERROR: Please provide the subnet endpoint private key!')
    process.exit(1)
  }

  if (!subnetLogoUrl) {
    console.error('ERROR: Please provide the subnet logo url!')
    process.exit(1)
  }

  if (!subnetName) {
    console.error('ERROR: Please provide the subnet name!')
    process.exit(1)
  }

  if (!subnetCurrencySymbol) {
    console.error('ERROR: Please provide the subnet currency symbol!')
    process.exit(1)
  }

  if (!subnetChainId) {
    console.error('ERROR: Please provide the subnet subnetChainId!')
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

  if (!utils.isHexString(subnetRegistratorAddress, 20)) {
    console.error(
      'ERROR: Please provide a valid SubnetRegistrator contract address!'
    )
    process.exit(1)
  }

  const wallet = new Wallet(toposDeployerPrivateKey, provider)

  const contract = new Contract(
    subnetRegistratorAddress,
    subnetRegistratorJSON.abi,
    wallet
  )

  const tx: ContractTransaction = await contract.registerSubnet(
    subnetRPCEndpoint,
    subnetLogoUrl,
    subnetName,
    subnetId,
    subnetCurrencySymbol,
    subnetChainId
  )

  await tx
    .wait()
    .then(() => {
      console.log(`Successfully registered the ${subnetName} subnet!`)
    })
    .catch((error: any) => {
      console.error(error)
    })
}

const sanitizeHexString = function (hexString: string) {
  return hexString.startsWith('0x') ? hexString : `0x${hexString}`
}

const args = process.argv.slice(2)
main(...args)
