import brownie

# const
APPROVE_AMOUNT = 10
CERT_BYTES = "0xdeaf"
CERT_POSITION = 5
CERT_ID = brownie.convert.to_bytes(CERT_BYTES, "bytes32")
DAILY_MINT_LIMIT = 100
TARGET_SUBNET_ID = brownie.convert.to_bytes("0x02", "bytes32")
DUMMY_DATA = brownie.convert.to_bytes("0x00", "bytes")
ENDPOINT = "http://127.0.0.1"
LOGO_URL = "http://image-url.com"
MINIMUM_CERT_POSITION = 4
MINT_AMOUNT = 10
MINT_CAP = 1000
SOURCE_SUBNET_ID = brownie.convert.to_bytes("0x01", "bytes32")
PAYLOAD = brownie.convert.to_bytes("0xdead", "bytes")
PEER_ID = brownie.convert.to_bytes("0xdeaf", "bytes")
SEND_AMOUNT = 10
SUBNET_BYTES = "0xdeaf"
SUBNET_NAME = "Test Subnet"
SUBNET_PUBLIC_KEY = brownie.convert.to_bytes(SUBNET_BYTES, "bytes")
SUBNET_CURRENCY_SYMBOL = "SUB"
TOKEN_NAME = "TokenX"
TOKEN_SYMBOL_X = "TKX"
TOKEN_SYMBOL_Y = "TKY"
# admin params
ADMIN_PARAMS = [
    "address[]",  # admin addresses
    "uint256",  # admin threshold
]
# token to be deployed params
TOKEN_PARAMS = [
    "string",  # name
    "string",  # symbol
    "uint256",  # cap
    "address",  # token address
    "uint256",  # daily mint limit
]
# token to mint params
MINT_TOKEN_PARAMS = [
    "bytes",  # tx hash
    "address",  # sender
    "bytes32",  # source subnet id
    "bytes32",  # target subnet id
    "address",  # receiver
    "string",  # symbol
    "uint256",  # amount
]
