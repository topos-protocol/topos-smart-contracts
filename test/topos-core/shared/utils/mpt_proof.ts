import { ethers } from 'ethers'
import { RLP } from '@ethereumjs/rlp'
import { Trie } from '@ethereumjs/trie'
import { BlockWithTransactions } from '@ethersproject/abstract-provider'

export async function getMptProof(
  tx: ethers.providers.TransactionResponse,
  provider: ethers.providers.JsonRpcProvider
) {
  const receipt = await provider.getTransactionReceipt(tx.hash)
  const block = await provider.getBlockWithTransactions(receipt.blockHash)
  const rawBlock = await provider.send('eth_getBlockByHash', [
    receipt.blockHash,
    true,
  ])
  const transactionsRoot = rawBlock.transactionsRoot

  const trie = await createTrie(block)
  const trieRoot = trie.root()
  if ('0x' + trieRoot.toString('hex') !== transactionsRoot) {
    throw new Error('Transactions root mismatch')
  }

  const indexOfTx = block.transactions.findIndex((_tx) => _tx.hash === tx.hash)
  const key = Buffer.from(RLP.encode(indexOfTx))

  const txRaw = getRawTransaction(tx)
  const indexOfTxData = txRaw.substring(2).indexOf(tx.data.substring(2)) / 2

  const { stack: _stack } = await trie.findPath(key)
  const stack = _stack.map((node) => node.raw())
  const proofBlob = ethers.utils.hexlify(RLP.encode([1, indexOfTx, stack]))
  return { indexOfTxData, proofBlob, transactionsRoot, txRaw }
}

async function createTrie(block: BlockWithTransactions) {
  const trie = new Trie()
  await Promise.all(
    block.transactions.map(async (tx, index) => {
      const { nonce, gasPrice, gasLimit, to, value, data, v, r, s } = tx
      return trie.put(
        Buffer.from(RLP.encode(index)),
        Buffer.from(
          RLP.encode([
            nonce,
            gasPrice?.toNumber(),
            gasLimit.toNumber(),
            to,
            value.toNumber(),
            data,
            v,
            r,
            s,
          ])
        )
      )
    })
  )
  return trie
}

function getRawTransaction(tx: ethers.providers.TransactionResponse): string {
  function addKey(accum, key) {
    if (tx[key as keyof typeof tx]) {
      accum[key] = tx[key as keyof typeof tx]
    }
    return accum
  }
  const txFields =
    'accessList chainId data gasPrice gasLimit maxFeePerGas maxPriorityFeePerGas nonce to type value'.split(
      ' '
    )
  const sigFields = 'v r s'.split(' ')
  const raw = ethers.utils.serializeTransaction(
    txFields.reduce(addKey, {}),
    sigFields.reduce(addKey, {})
  )
  if (ethers.utils.keccak256(raw) !== tx.hash) {
    throw new Error('serializing failed!')
  }
  return raw
}
