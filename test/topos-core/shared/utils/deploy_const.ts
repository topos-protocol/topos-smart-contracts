import { deployContractConstant } from '@axelar-network/axelar-gmp-sdk-solidity'
import { SignerWithAddress } from '@nomiclabs/hardhat-ethers/signers'

type Abi = {
  inputs: {
    internalType: string
    name: string
    type: string
  }[]
  name: string
  outputs: {
    internalType: string
    name: string
    type: string
  }[]
  stateMutability: string
  type: string
}

export async function deployConstAddress(
  constAddressDeployerAddr: string,
  wallet: SignerWithAddress,
  contractJson: {
    _format: string
    contractName: string
    sourceName: string
    abi: Abi[]
    bytecode: string
    deployedBytecode: string
    linkReferences: object
    deployedLinkReferences: object
  },
  salt: string,
  args: never[],
  gasLimit = 0
) {
  return deployContractConstant(
    constAddressDeployerAddr,
    wallet,
    contractJson,
    salt,
    args,
    gasLimit === 0 ? null : gasLimit
  )
    .then((contract: { address: unknown }) => contract.address)
    .catch((error: Error) => {
      console.error(error)
      process.exit(1)
    })
}
