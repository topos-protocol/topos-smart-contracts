import { ethers } from 'ethers'
import { RLP } from '@ethereumjs/rlp'
import { Trie } from '@ethereumjs/trie'
import { BlockWithTransactions } from '@ethersproject/abstract-provider'

export async function getReceiptMptProof(
  tx: ethers.providers.TransactionResponse,
  provider: ethers.providers.JsonRpcProvider
) {
  const receipt = await provider.getTransactionReceipt(tx.hash)
  const block = await provider.getBlockWithTransactions(receipt.blockHash)
  const rawBlock = await provider.send('eth_getBlockByHash', [
    receipt.blockHash,
    true,
  ])

  const receiptsRoot = rawBlock.receiptsRoot
  const trie = await createTrie(block)
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

  const indexOfTx = block.transactions.findIndex((_tx) => _tx.hash === tx.hash)
  const key = Buffer.from(RLP.encode(indexOfTx))

  const { stack: _stack } = await trie.findPath(key)
  const stack = _stack.map((node) => node.raw())
  const proofBlob = ethers.utils.hexlify(RLP.encode([1, indexOfTx, stack]))
  return { proofBlob, receiptsRoot }
}

async function createTrie(block: BlockWithTransactions) {
  const trie = new Trie()
  await Promise.all(
    block.transactions.map(async (tx, index) => {
      const { /*type,*/ cumulativeGasUsed, logs, logsBloom, status } =
        await tx.wait()
      // console.log('Tx type: ', type)
      // console.log('status: ', status)
      // console.log('cumulativeGasUsed: ', cumulativeGasUsed)
      // console.log('logsBloom: ', logsBloom)
      // console.log('logs: ', logs)

      return trie.put(
        Buffer.from(RLP.encode(index)),
        Buffer.from(
          RLP.encode([
            status,
            cumulativeGasUsed.toNumber(),
            logsBloom,
            logs.map((l) => [l.address, l.topics, l.data]),
          ])
        )
      )
    })
  )
  return trie
}
