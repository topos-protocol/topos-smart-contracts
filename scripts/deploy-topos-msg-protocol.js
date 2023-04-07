const axelarUtils = require('@axelar-network/axelar-gmp-sdk-solidity')
const ethers = require('ethers')

const tokenDeployerJSON = require('../artifacts/contracts/topos-core/TokenDeployer.sol/TokenDeployer.json')
const toposCoreJSON = require('../artifacts/contracts/topos-core/ToposCore.sol/ToposCore.json')
const toposCoreProxyJSON = require('../artifacts/contracts/topos-core/ToposCoreProxy.sol/ToposCoreProxy.json')
const toposCoreInterfaceJSON = require('../artifacts/contracts/interfaces/IToposCore.sol/IToposCore.json')

const CONST_ADDRESS_DEPLOYER_ADDR = '0x0000000000000000000000000000000000001110'

const main = async function (endpoint, _sequencerPrivateKey) {
  const provider = new ethers.providers.JsonRpcProvider(endpoint)
  const toposDeployerPrivateKey = sanitizeHexString(process.env.PRIVATE_KEY)
  const tokenDeployerSalt = process.env.TOKEN_DEPLOYER_SALT
  const toposCoreSalt = process.env.TOPOS_CORE_SALT
  const toposCoreProxySalt = process.env.TOPOS_CORE_PROXY_SALT

  if (!_sequencerPrivateKey) {
    console.error('ERROR: Please provide the sequencer private key!')
    process.exit(1)
  }

  const sequencerPrivateKey = sanitizeHexString(_sequencerPrivateKey)

  if (!ethers.utils.isHexString(sequencerPrivateKey, 32)) {
    console.error('ERROR: The sequencer private key is not a valid key!')
    process.exit(1)
  }

  const isCompressed = true
  const sequencerPublicKey = ethers.utils.computePublicKey(
    sequencerPrivateKey,
    isCompressed
  )

  const subnetId = sanitizeHexString(sequencerPublicKey.substring(4))
  console.log('Subnet Id:', subnetId)

  if (
    !toposDeployerPrivateKey ||
    !ethers.utils.isHexString(toposDeployerPrivateKey, 32)
  ) {
    console.error(
      'ERROR: Please provide a valid toposDeployer private key! (PRIVATE_KEY)'
    )
    process.exit(1)
  }

  if (!tokenDeployerSalt) {
    console.error(
      'ERROR: Please provide a salt for TokenDeployer! (TOKEN_DEPLOYER_SALT)'
    )
    process.exit(1)
  }

  if (!toposCoreSalt) {
    console.error(
      'ERROR: Please provide a salt for ToposCore! (TOPOS_CORE_SALT)'
    )
    return
  }

  if (!toposCoreProxySalt) {
    console.error(
      'ERROR: Please provide a salt for ToposCoreProxy! (TOPOS_CORE_PROXY_SALT)'
    )
    process.exit(1)
  }

  const wallet = new ethers.Wallet(toposDeployerPrivateKey, provider)

  const tokenDeployerAddress = await processContract(
    'TokenDeployer',
    wallet,
    tokenDeployerJSON,
    tokenDeployerSalt
  )

  const toposCoreAddress = await processContract(
    'ToposCore',
    wallet,
    toposCoreJSON,
    toposCoreSalt,
    [tokenDeployerAddress],
    4_000_000
  )

  const toposCoreProxyParams = ethers.utils.defaultAbiCoder.encode(
    ['address[]', 'uint256'],
    [[wallet.address], 1] // TODO: Use a different admin address than ToposDeployer
  )
  const toposCoreProxyAddress = await processContract(
    'ToposCoreProxy',
    wallet,
    toposCoreProxyJSON,
    toposCoreProxySalt,
    [toposCoreAddress, toposCoreProxyParams],
    4_000_000
  )

  console.info(`\nSetting subnetId on ToposCore via proxy`)
  const toposCoreInterface = new ethers.Contract(
    toposCoreProxyAddress,
    toposCoreInterfaceJSON.abi,
    wallet
  )
  await toposCoreInterface
    .setNetworkSubnetId(subnetId, { gasLimit: 4_000_000 })
    .then(async (tx) => {
      await tx.wait().catch((error) => {
        console.error(
          `Error: Failed (wait) to set ${subnetId} subnetId on ToposCore via proxy!`
        )
        console.error(error)
        process.exit(1)
      })
    })
    .catch((error) => {
      console.error(
        `Error: Failed to set ${subnetId} subnetId on ToposCore via proxy!`
      )
      console.error(error)
      process.exit(1)
    })
  const networkSubnetId = await toposCoreInterface.networkSubnetId()
  console.info(
    `Successfully set ${networkSubnetId} subnetId on ToposCore via proxy\n`
  )
}

const sanitizeHexString = function (hexString) {
  return hexString.startsWith('0x') ? hexString : `0x${hexString}`
}

const deployConstAddress = function (
  wallet,
  contractJson,
  salt,
  args,
  gasLimit
) {
  return axelarUtils
    .deployContractConstant(
      CONST_ADDRESS_DEPLOYER_ADDR,
      wallet,
      contractJson,
      salt,
      args,
      gasLimit === 0 ? null : gasLimit
    )
    .then((contract) => contract.address)
    .catch((error) => {
      console.error(error)
      process.exit(1)
    })
}

const predictContractAddress = function (wallet, contractJson, salt, args) {
  return axelarUtils
    .predictContractConstant(
      CONST_ADDRESS_DEPLOYER_ADDR,
      wallet,
      contractJson,
      salt,
      args
    )
    .catch((error) => {
      console.error(error)
      process.exit(1)
    })
}

const processContract = async function (
  contractName,
  wallet,
  contractJson,
  salt,
  args = [],
  gasLimit = 0
) {
  console.info(`\nVerifying if ${contractName} is already deployed...`)

  const predictedContractAddress = await predictContractAddress(
    wallet,
    contractJson,
    salt,
    args
  )

  const codeAtPredictedAddress = await wallet.provider.getCode(
    predictedContractAddress
  )

  const thereIsCodeAtAddress = codeAtPredictedAddress !== '0x'

  if (thereIsCodeAtAddress) {
    console.info(
      `${contractName} is already deployed! (${predictedContractAddress})`
    )

    return predictedContractAddress
  } else {
    console.info(`Deploying ${contractName} with constant address...`)

    const newContractAddress = await deployConstAddress(
      wallet,
      contractJson,
      salt,
      args,
      gasLimit
    )

    if (newContractAddress !== predictedContractAddress) {
      console.error(
        `ERROR: New contract address doesn't match the predicted address! (New: ${newContractAddress} | Predicted: ${predictedContractAddress})`
      )
      process.exit(1)
    }

    console.info(
      `Successfully deployed ${contractName} at ${newContractAddress}\n`
    )

    return newContractAddress
  }
}

const args = process.argv.slice(2)
main(...args)
