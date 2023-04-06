const axelarUtils = require('@axelar-network/axelar-gmp-sdk-solidity')
const ethers = require('ethers')
const fs = require('fs')

const CONST_ADDRESS_DEPLOYER_ADDR = '0x0000000000000000000000000000000000001110'

const main = async function (
  endpoint,
  contractJsonPath,
  salt,
  gasLimit = 0,
  ...args
) {
  const provider = new ethers.providers.JsonRpcProvider(endpoint)
  const privateKey = process.env.PRIVATE_KEY

  if (!privateKey || !ethers.utils.isHexString(privateKey, 32)) {
    console.error('ERROR: Please provide a valid private key! (PRIVATE_KEY)')
    return
  }

  const wallet = new ethers.Wallet(process.env.PRIVATE_KEY, provider)

  let rawdata
  try {
    rawdata = fs.readFileSync(contractJsonPath)
  } catch (error) {
    console.error(
      `ERROR: Could not find a contract JSON file at ${contractJsonPath}`
    )
    return
  }

  let contractJson
  try {
    contractJson = JSON.parse(rawdata)
  } catch (error) {
    console.error(
      `ERROR: Could not parse the contract JSON file found at ${contractJsonPath}`
    )
    return
  }

  axelarUtils
    .deployContractConstant(
      CONST_ADDRESS_DEPLOYER_ADDR,
      wallet,
      contractJson,
      salt,
      args,
      gasLimit === 0 ? null : gasLimit
    )
    .then((contract) => {
      console.info(
        `Successfully deployed ${contractJsonPath.split('.json')[0]} at ${
          contract.address
        }`
      )
    })
    .catch(console.error)
}

const args = process.argv.slice(2)
main(...args)
