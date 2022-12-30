const axelarUtils = require('@axelar-network/axelar-gmp-sdk-solidity');
const ethers = require('ethers');
const fs = require('fs');

const CONST_ADDRESS_DEPLOYER_ADDR =
  '0x0000000000000000000000000000000000001110';

const main = async function (endpoint, contractJsonPath, salt = '', args = []) {
  const provider = new ethers.providers.JsonRpcProvider(endpoint);

  provider
    .getCode(CONST_ADDRESS_DEPLOYER_ADDR)
    .then(console.log)
    .catch(console.error);
  const wallet = new ethers.Wallet(process.env.PRIVATE_KEY, provider);

  let rawdata = fs.readFileSync(contractJsonPath);
  let contractJson = JSON.parse(rawdata);

  axelarUtils
    .deployContractConstant(
      CONST_ADDRESS_DEPLOYER_ADDR,
      wallet,
      contractJson,
      salt,
      args,
      (gasLimit = null),
    )
    .catch(console.error);
};

const args = process.argv.slice(2);
main(...args);
