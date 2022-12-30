const axelarUtils = require('@axelar-network/axelar-gmp-sdk-solidity');
const checksum = require('checksum');
const ethers = require('ethers');
const fs = require('fs');

const CONST_ADDRESS_DEPLOYER_ADDR =
  '0x0000000000000000000000000000000000001110';

const main = async function (
  endpoint,
  contractJsonPath,
  salt,
  gasLimit = 0,
  ...args
) {
  const provider = new ethers.providers.JsonRpcProvider(endpoint);
  const wallet = new ethers.Wallet(process.env.PRIVATE_KEY, provider);

  let rawdata = fs.readFileSync(contractJsonPath);
  let contractJson = JSON.parse(rawdata);

  console.log('ConstAddressDeployer address: ', CONST_ADDRESS_DEPLOYER_ADDR);
  console.log('Wallet: ', wallet.address);
  console.log('contractJson: ', checksum(JSON.stringify(contractJson)));
  console.log('salt: ', salt);
  console.log('args: ', args);
  console.log('gasLimit: ', gasLimit);

  axelarUtils
    .deployContractConstant(
      CONST_ADDRESS_DEPLOYER_ADDR,
      wallet,
      contractJson,
      salt,
      args,
      gasLimit === 0 ? null : gasLimit,
    )
    .then((contract) => {
      console.info(
        `Successfully deployed ${contractJsonPath.split('.json')[0]} at ${
          contract.address
        }`,
      );
    })
    .catch(console.error);
};

const args = process.argv.slice(2);
main(...args);
