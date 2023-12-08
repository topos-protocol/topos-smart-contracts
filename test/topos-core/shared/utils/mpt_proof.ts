import { Block, hexlify, JsonRpcProvider, TransactionResponse } from 'ethers'
import { RLP } from '@ethereumjs/rlp'
import { Trie } from '@ethereumjs/trie'

export async function getReceiptMptProof(
  tx: TransactionResponse,
  provider: JsonRpcProvider
) {
  const receipt = await provider.getTransactionReceipt(tx.hash)
  const prefectTxs = true
  const block = await provider.getBlock(receipt!.blockHash, prefectTxs)
  const rawBlock = await provider.send('eth_getBlockByHash', [
    receipt!.blockHash,
    true,
  ])

  const receiptsRoot = rawBlock.receiptsRoot
  const trie = await createTrie(block!, provider)
  const trieRoot = trie.root()
  if ('0x' + trieRoot.toString('hex') !== receiptsRoot) {
    throw new Error(
      'Receipts root does not match trie root' +
        '\n' +
        'trieRoot: ' +
        '0x' +
        trieRoot.toString('hex') +
        '\n' +
        'receiptsRoot: ' +
        receiptsRoot
    )
  }

  const indexOfTx = block!.prefetchedTransactions.findIndex(
    (_tx) => _tx.hash === tx.hash
  )
  const key = Buffer.from(RLP.encode(indexOfTx))

  const { stack: _stack } = await trie.findPath(key)
  const stack = _stack.map((node) => node.raw())
  const proofBlob = hexlify(RLP.encode([1, indexOfTx, stack]))
  return { proofBlob, receiptsRoot }
}

async function createTrie(block: Block, provider: JsonRpcProvider) {
  const trie = new Trie()
  await Promise.all(
    block.prefetchedTransactions.map(async (tx, index) => {
      const receipt = await provider.getTransactionReceipt(tx.hash)
      const { cumulativeGasUsed, logs, logsBloom, status } = receipt!
      return trie.put(
        Buffer.from(RLP.encode(index)),
        Buffer.from(
          RLP.encode([
            status,
            Number(cumulativeGasUsed),
            logsBloom,
            logs.map((l) => [l.address, <string[]>l.topics, l.data]),
          ])
        )
      )
    })
  )
  return trie
}
