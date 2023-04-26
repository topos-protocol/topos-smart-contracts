import { providers, utils, Wallet } from 'ethers'
import fs from 'fs'

import {
  Arg,
  ContractOutputJSON,
  deployContractConstant,
} from './const-addr-deployer'

const main = async function (..._args: Arg[]) {
  const [providerEndpoint, contractJsonPath, salt, gasLimit, ...args] = _args
  const provider = new providers.JsonRpcProvider(<string>providerEndpoint)
  const privateKey = process.env.PRIVATE_KEY

  if (!privateKey || !utils.isHexString(privateKey, 32)) {
    console.error('ERROR: Please provide a valid private key! (PRIVATE_KEY)')
    return
  }

  const wallet = new Wallet(process.env.PRIVATE_KEY || '', provider)

  let rawdata
  try {
    rawdata = fs.readFileSync(contractJsonPath)
  } catch (error) {
    console.error(
      `ERROR: Could not find a contract JSON file at ${contractJsonPath}`
    )
    return
  }

  let contractJson: ContractOutputJSON
  try {
    contractJson = JSON.parse(rawdata.toString())
  } catch (error) {
    console.error(
      `ERROR: Could not parse the contract JSON file found at ${contractJsonPath}`
    )
    return
  }

  await deployContractConstant(
    wallet,
    contractJson,
    <string>salt,
    args,
    <number>gasLimit
  )
    .then((contract) => {
      console.info(
        `Successfully deployed ${
          (<string>contractJsonPath).split('.json')[0]
        } at ${contract.address}`
      )

      process.stdout.write(contract.address)
    })
    .catch(console.error)
}

const args = process.argv.slice(2)
main(...args)
