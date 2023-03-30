#!/usr/bin/env python3

import json
import rlp
import sys

from trie import HexaryTrie
from trie.constants import (
    NODE_TYPE_BLANK,
    NODE_TYPE_LEAF,
    NODE_TYPE_EXTENSION,
    NODE_TYPE_BRANCH,
)
from trie.utils.nibbles import bytes_to_nibbles
from trie.utils.nodes import consume_common_prefix, extract_key, get_node_type
from web3 import Web3
from eth_account._utils.legacy_transactions import (
    encode_transaction,
    serializable_unsigned_transaction_from_dict,
)
from web3.middleware import geth_poa_middleware

# constants
ACCESS_LIST = "accessList"
BLOCK_NUMBER = "blockNumber"
BLOCK_TXNS = "block_txns"
CHAIN_ID = "chainId"
DATA = "data"
GAS = "gas"
GAS_PRICE = "gasPrice"
HASH = "hash"
INPUT = "input"
MAX_FEE_PER_GAS = "maxFeePerGas"
MAX_PRIORITY_FEE_PER_GAS = "maxPriorityFeePerGas"
NONCE = "nonce"
PROOF_BLOB = "proof_blob"
PROOF_TYPE = 1
TO = "to"
TRANSACTION_INDEX = "transactionIndex"
TRANSACTIONS = "transactions"
TRANSACTIONS_ROOT = "transactionsRoot"
TX_INDEX = "tx_index"
TX_RAW = "tx_raw"
TX_TYPE = "type"
TXNS_ROOT = "txns_root"
VALUE = "value"


def generate_proof(mpt, mpt_key_nibbles: bytes):
    """
    Generates a Merkle Patricia Trie proof for a given key nibble sequence.

    Args:
        mpt: A HexaryTrie object
        mpt_key_nibbles: The key nibble sequence to generate a proof for

    Returns:
        A list of nodes in the proof required to reconstruct the value at the
        key nibble sequence.
    """
    # Ensure that all nibble elements in the sequence are valid (between 0~15)
    if not all(0 <= nibble < 16 for nibble in mpt_key_nibbles):
        raise ValueError(
            "mpt_key_nibbles has non-nibble elements {}".format(
                str(mpt_key_nibbles)
            )
        )

    # Variables for tracking proof nodes
    stack_indexes = []  # Tracks the indexes of each node on the stack
    stack = []  # Stack of nodes needed for the proof

    def aux(node_hash, mpt_key_nibbles):
        """
        Recursive function to traverse the MPT.

        Args:
            node_hash: The hash of the current node
            mpt_key_nibbles: The remaining key nibble sequence to traverse

        Returns:
            None
        """
        nonlocal stack_indexes  # Allow access to parent scope's variables
        nonlocal stack

        # Get the current node
        node = mpt.get_node(node_hash)

        # If the node is blank, do nothing
        if get_node_type(node) == NODE_TYPE_BLANK:
            return
        # If the node is a branch, traverse its children
        elif get_node_type(node) == NODE_TYPE_BRANCH:
            if mpt_key_nibbles:
                # If there are nibbles remaining, get the next nibble and
                # traverse the corresponding child node
                i = mpt_key_nibbles[0]
                stack_indexes.append(i)
                stack.append(node)
                aux(node[i], mpt_key_nibbles[1:])
            else:
                # If there are no nibbles remaining, traverse the empty branch
                i = 16
                stack_indexes.append(i)
                stack.append(node)
        # If the node is an extension or a leaf,consume its prefix and
        # traverse the corresponding child node
        elif get_node_type(node) in [NODE_TYPE_EXTENSION, NODE_TYPE_LEAF]:
            key = extract_key(node)
            (
                prefix,
                key_remainder,
                mpt_key_nibbles_remainder,
            ) = consume_common_prefix(key, mpt_key_nibbles)
            if not key_remainder:
                # If the key is consumed, add the node to the stack
                stack_indexes.append(1)
                stack.append(node)
                # If the node is an extension, traverse its child node
                if get_node_type(node) == NODE_TYPE_EXTENSION:
                    aux(node[1], mpt_key_nibbles_remainder)
            else:
                # If the key is not yet consumed, add the node to the stack
                stack_indexes.append(0xFF)
                stack.append(node)
        else:
            # If the node type is unknown, raise an error
            raise ValueError(
                "Unknown node type: {}".format(get_node_type(node))
            )

    # Get the root node and traverse the MPT to generate the proof
    root_node = mpt.get_node(mpt.root_hash)
    if get_node_type(root_node) == NODE_TYPE_BLANK:
        None
    else:
        aux(mpt.root_hash, mpt_key_nibbles)
    return stack


def get_merkle_proof(block_txns, tx_index, tx_raw, txns_root):
    # Create a new trie
    trie = HexaryTrie(db={})

    # Add each transaction in the block to the trie
    for block_tx in block_txns:
        trie.set(
            rlp.encode(block_tx[TX_INDEX]),
            bytes.fromhex(block_tx[TX_RAW]),
        )

    # Verify that the calculated root matches the provided root
    lib_txns_root = trie.root_hash.hex()
    assert txns_root == "0x" + lib_txns_root

    # Convert the transaction index to nibbles
    mpt_key_nibbles = bytes_to_nibbles(rlp.encode(tx_index))

    # Generate the proof stack for the transaction
    stack = generate_proof(trie, mpt_key_nibbles)

    # Encode the proof as an RLP list with the type 1
    # (indicating a transaction proof)
    proof_blob = rlp.encode(
        [
            PROOF_TYPE,
            tx_index,
            stack,
        ]
    ).hex()
    print_json_output(proof_blob, tx_raw, txns_root)
    return proof_blob, tx_raw, txns_root


def get_tx_data(endpoint, tx_hash):
    # Connect to endpoint and get transaction
    w3 = Web3(Web3.HTTPProvider(endpoint))
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    tx = w3.eth.get_transaction(tx_hash)

    # Recover raw transaction
    tx_raw = recover_raw_tx(tx)

    # Get transaction index
    tx_index = int(tx[TRANSACTION_INDEX])

    # Get sibling transactions
    block = w3.eth.get_block(int(tx[BLOCK_NUMBER]), True)
    block_txns = [
        {
            TX_INDEX: block_tx[TRANSACTION_INDEX],
            TX_RAW: recover_raw_tx(
                w3.eth.get_transaction(block_tx[HASH].hex())
            ).hex(),
        }
        for block_tx in block[TRANSACTIONS]
    ]

    # Get block transactionsRoot
    txns_root = block[TRANSACTIONS_ROOT].hex()

    return get_merkle_proof(block_txns, tx_index, tx_raw, txns_root)


def recover_raw_tx(tx_json):
    # Define tx based on tx type
    tx_type = int(tx_json.get(TX_TYPE, "0"), 16)
    if tx_type == 0:  # Legacy
        tx = {
            NONCE: int(tx_json[NONCE]),
            GAS_PRICE: int(tx_json[GAS_PRICE]),
            GAS: int(tx_json[GAS]),
            TO: tx_json[TO],
            VALUE: int(tx_json[VALUE]),
            DATA: tx_json[INPUT],
        }
    elif tx_type == 1:  # EIP-2930
        tx = {
            CHAIN_ID: tx_json[CHAIN_ID],
            NONCE: int(tx_json[NONCE]),
            GAS_PRICE: int(tx_json[GAS_PRICE]),
            GAS: int(tx_json[GAS]),
            TO: tx_json[TO],
            VALUE: int(tx_json[VALUE]),
            DATA: tx_json[INPUT],
            ACCESS_LIST: tx_json[ACCESS_LIST],
        }
    elif tx_type == 2:  # EIP-1559
        tx = {
            TX_TYPE: tx_type,
            CHAIN_ID: tx_json[CHAIN_ID],
            NONCE: int(tx_json[NONCE]),
            MAX_PRIORITY_FEE_PER_GAS: int(tx_json[MAX_PRIORITY_FEE_PER_GAS]),
            MAX_FEE_PER_GAS: int(tx_json[MAX_FEE_PER_GAS]),
            GAS: int(tx_json[GAS]),
            TO: tx_json[TO],
            VALUE: int(tx_json[VALUE]),
            DATA: tx_json[INPUT],
            ACCESS_LIST: tx_json[ACCESS_LIST],
        }
    else:
        raise ValueError(f"Unsupported tx type: {tx_type}")

    # Convert v, r, s to integers
    v = int(tx_json["v"])
    r = int(tx_json["r"].hex()[2:], 16)
    s = int(tx_json["s"].hex()[2:], 16)

    # Convert tx to serializable unsigned transaction and encode it
    unsigned_tx = serializable_unsigned_transaction_from_dict(tx)
    encoded_tx = encode_transaction(unsigned_tx, vrs=(v, r, s))

    return encoded_tx


def print_json_output(proof_blob, tx_raw, txns_root):
    output = json.dumps(
        {PROOF_BLOB: proof_blob, TX_RAW: tx_raw.hex(), TXNS_ROOT: txns_root}
    )
    print(output)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("Please provide 2 arguments")
    get_tx_data(endpoint=sys.argv[1], tx_hash=sys.argv[2])
