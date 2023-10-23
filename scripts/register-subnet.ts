import { Contract, ContractTransaction, providers, utils, Wallet } from 'ethers'

import subnetRegistratorJSON from '../artifacts/contracts/topos-core/SubnetRegistrator.sol/SubnetRegistrator.json'

const main = async function (...args: string[]) {
  const [
    toposSubnetProviderEndpoint,
    subnetRegistratorAddress,
    subnetName,
    subnetChainId,
    subnetEndpointHttp,
    subnetEndpointWs,
    subnetCurrencySymbol,
    subnetLogoUrl,
    _adminPrivateKey,
    _sequencerPrivateKey,
  ] = args
  const provider = new providers.JsonRpcProvider(toposSubnetProviderEndpoint)

  if (!_adminPrivateKey) {
    console.error(
      'ERROR: Please provide the SubnetRegistrator admin private key!'
    )
    process.exit(1)
  }

  if (!_sequencerPrivateKey) {
    console.error('ERROR: Please provide the sequencer private key!')
    process.exit(1)
  }

  if (!subnetEndpointHttp) {
    console.error('ERROR: Please provide the subnet HTTP endpoint!')
    process.exit(1)
  }

  if (!subnetEndpointWs) {
    console.error('ERROR: Please provide the subnet WS endpoint!')
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

  const adminPrivateKey = sanitizeHexString(_adminPrivateKey)

  if (!utils.isHexString(adminPrivateKey, 32)) {
    console.error('ERROR: The admin private key is not a valid key!')
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

  const wallet = new Wallet(adminPrivateKey, provider)

  const contract = new Contract(
    subnetRegistratorAddress,
    subnetRegistratorJSON.abi,
    wallet
  )

  const alreadyRegisteredSubnet = await verifyIfSubnetAlreadyRegistered(
    contract,
    subnetId
  )
  if (alreadyRegisteredSubnet.name) {
    console.log(
      `${alreadyRegisteredSubnet.name} is already registered with ${subnetId} subnet id!`
    )
    process.exit(0)
  }

  const tx: ContractTransaction = await contract.registerSubnet(
    subnetChainId,
    subnetCurrencySymbol,
    subnetEndpointHttp,
    subnetEndpointWs,
    subnetLogoUrl,
    subnetName,
    subnetId,
    { gasLimit: 4_000_000 }
  )

  await tx
    .wait()
    .then(() => {
      console.log(`Successfully registered the ${subnetName} subnet!`)
    })
    .catch((error) => {
      console.error(error)
    })
}

const sanitizeHexString = function (hexString: string) {
  return hexString.startsWith('0x') ? hexString : `0x${hexString}`
}

const verifyIfSubnetAlreadyRegistered = function (
  contract: Contract,
  subnetId: string
) {
  return contract.subnets(subnetId) as Promise<{ name: string }>
}

const args = process.argv.slice(2)
main(...args)
