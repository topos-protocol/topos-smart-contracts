import sys
import web3
from eth_account._utils.legacy_transactions import (
    encode_transaction,
    serializable_unsigned_transaction_from_dict,
)


def recover_raw_transaction_type_2(tx):
    """
    Only supports legacy transactions
    """
    transaction = {
        # "chainId": tx["chainId"], # type 2 eth tx
        "nonce": int(tx["nonce"]),
        # "maxPriorityFeePerGas": int(tx["maxPriorityFeePerGas"]),
        # "maxFeePerGas": int(tx["maxFeePerGas"]),
        "gasPrice": int(tx["gasPrice"]),
        "gas": int(tx["gas"]),
        "to": tx["to"],
        "value": int(tx["value"]),
        "data": tx["input"],
        # "accessList": tx["accessList"],
    }

    v = int(tx["v"])
    r = int(tx["r"].hex()[2:], 16)
    s = int(tx["s"].hex()[2:], 16)
    unsigned_transaction = serializable_unsigned_transaction_from_dict(
        transaction
    )
    encoded_transaction = encode_transaction(
        unsigned_transaction, vrs=(v, r, s)
    ).hex()
    return encoded_transaction


def get_transaction_hash(w3, hash):
    transaction = w3.eth.getTransaction(hash)
    transaction_hex = recover_raw_transaction_type_2(transaction)
    print(transaction_hex)
    return transaction_hex


def get_raw_transaction_positional_args(*args):
    if len(args) != 2:
        raise Exception(
            f"Please provide arguments: provided: {len(args)}, required: 2"
        )
    w3 = web3.Web3(web3.HTTPProvider(args[0]))
    hash = args[1]
    return get_transaction_hash(w3, hash)


def get_raw_transaction_system_args():
    args = sys.argv[1:]
    if len(args) != 2:
        raise Exception(
            f"Please provide arguments: provided: {len(args)}, required: 2"
        )
    w3 = web3.Web3(web3.HTTPProvider(args[0]))
    hash = args[1]
    return get_transaction_hash(w3, hash)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        get_raw_transaction_system_args()
    else:
        get_raw_transaction_positional_args()
