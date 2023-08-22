import { Contract, providers, utils, Wallet, constants } from 'ethers'
import { keccak256 } from '@ethersproject/keccak256'
import { toUtf8Bytes } from '@ethersproject/strings'

import erc20MessagingJSON from '../../artifacts/contracts/examples/ERC20Messaging.sol/ERC20Messaging.json'
import toposCoreInterfaceJSON from '../../artifacts/contracts/interfaces/IToposCore.sol/IToposCore.json'
import ERC20 from '../../artifacts/@openzeppelin/contracts/token/ERC20/ERC20.sol/ERC20.json'

import * as cc from '../../test/topos-core/shared/constants/certificates'
import * as tc from '../../test/topos-core/shared/constants/tokens'
import * as testUtils from '../../test/topos-core/shared/utils/common'

/// Usage:
/// ts-node ./scripts/test/send-token.ts <node endpoint> <sender private key> <receiver account> <amount>
/// e.g.:
/// reset; ts-node ./scripts/test/send-token.ts http://127.0.0.1:8545 0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80 0x70997970C51812dc3A010C7d01b50e0d17dc79C8 10
const main = async function (...args: string[]) {
  const [providerEndpoint, senderPrivateKey, receiverAddress, amount] = args
  const provider = providers.getDefaultProvider(providerEndpoint)
  const erc20MessagingAddress = sanitizeHexString(
    process.env.ERC20_MESSAGING_ADDRESS || ''
  )

  if (!utils.isHexString(erc20MessagingAddress, 20)) {
    console.error(
      'ERROR: Please set token deployer contract address ERC20_MESSAGING_ADDRESS'
    )
    process.exit(1)
  }

  const toposCoreProxyAddress = sanitizeHexString(
    process.env.TOPOS_CORE_PROXY_ADDRESS || ''
  )

  if (!utils.isHexString(toposCoreProxyAddress, 20)) {
    console.error(
      'ERROR: Please set topos core proxy contract address  TOPOS_CORE_PROXY_ADDRESS'
    )
    process.exit(1)
  }

  const wallet = new Wallet(senderPrivateKey, provider)

  const erc20Messaging = new Contract(
    erc20MessagingAddress,
    erc20MessagingJSON.abi,
    wallet
  )
  const toposCoreProxy = new Contract(
    toposCoreProxyAddress,
    toposCoreInterfaceJSON.abi,
    wallet
  )

  const id = await toposCoreProxy.networkSubnetId()
  console.log('Network subnet id=', id)

  const defaultToken = testUtils.encodeTokenParam(
    tc.TOKEN_NAME,
    tc.TOKEN_SYMBOL_X,
    tc.MINT_CAP_100_000_000,
    constants.AddressZero,
    tc.DAILY_MINT_LIMIT_100,
    tc.INITIAL_SUPPLY_10_000_000
  )

  let deploy = true
  let tokenAddress = null
  // Check if token is already deployed. If not, deploy it
  const numberOfTokens = await erc20Messaging.getTokenCount()
  for (let index = 0; index < numberOfTokens; index++) {
    const tokenKey = await erc20Messaging.getTokenKeyAtIndex(index)
    const [token, address] = await erc20Messaging.tokens(tokenKey)
    if (token == tc.TOKEN_SYMBOL_X) {
      deploy = false
      console.log(
        'Token already deployed, token key:',
        tokenKey,
        ' token:',
        token,
        ' address:',
        address
      )
      tokenAddress = address
    }
  }

  if (deploy) {
    // Deploy token if not previously deployed
    const tx = await erc20Messaging.deployToken(defaultToken, {
      gasLimit: 5_000_000,
    })
    const txReceipt = await tx.wait()
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const logs = txReceipt.events?.find((e: any) => e.event === 'TokenDeployed')

    tokenAddress = logs?.args?.tokenAddress
    console.log(
      'Token:',
      tc.TOKEN_SYMBOL_X,
      ' deployed to address:',
      tokenAddress
    )
  }

  // Approve token burn
  const erc20 = new Contract(tokenAddress, ERC20.abi, wallet)
  await erc20.approve(erc20Messaging.address, amount)

  // Send token
  console.log(
    'Sending token:',
    tc.TOKEN_SYMBOL_X,
    ' from:',
    wallet.address,
    ' to:',
    receiverAddress,
    ' amount:',
    amount,
    ' token address:',
    tokenAddress
  )
  const tx = await erc20Messaging.sendToken(
    cc.TARGET_SUBNET_ID_4,
    tokenAddress,
    receiverAddress,
    amount,
    {
      gasLimit: 5_000_000,
    }
  )
  const txReceipt = await tx.wait()
  const logs = txReceipt.events?.find(
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    (e: any) =>
      e.topics[0] === keccak256(toUtf8Bytes('CrossSubnetMessageSent(bytes32)')) // For some reason e.events is not filled
  )

  if (logs) {
    console.log(
      'Token sent, from:',
      wallet.address,
      ' to:',
      receiverAddress,
      ' amount:',
      amount
    )

    const remainingBalance = await erc20.balanceOf(wallet.address)
    console.log('Remaining balance:', remainingBalance.toString())
  } else {
    console.log('Missing CrossSubnetMessageSent event')
  }
}

const sanitizeHexString = function (hexString: string) {
  return hexString.startsWith('0x') ? hexString : `0x${hexString}`
}

const args = process.argv.slice(2)
main(...args)
