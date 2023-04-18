import { ethers } from 'hardhat'

function encodeCertParam(
  prevId: string,
  sourceSubnetId: string,
  stateRoot: string,
  txRoot: string,
  targetSubnets: string[],
  verifier: number,
  certId: string,
  starkProof: string,
  signature: string
) {
  return ethers.utils.defaultAbiCoder.encode(
    [
      'bytes32',
      'bytes32',
      'bytes32',
      'bytes32',
      'bytes32[]',
      'uint32',
      'bytes32',
      'bytes',
      'bytes',
    ],
    [
      prevId,
      sourceSubnetId,
      stateRoot,
      txRoot,
      targetSubnets,
      verifier,
      certId,
      starkProof,
      signature,
    ]
  )
}

function encodeTokenParam(
  tokenName: string,
  tokenSymbol: string,
  mintCap: number,
  address: string,
  dailyMintLimit: number
) {
  return ethers.utils.defaultAbiCoder.encode(
    ['string', 'string', 'uint256', 'address', 'uint256'],
    [tokenName, tokenSymbol, mintCap, address, dailyMintLimit]
  )
}

export { encodeCertParam, encodeTokenParam }