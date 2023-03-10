const axelarUtils = require('@axelar-network/axelar-gmp-sdk-solidity');
const ethers = require('ethers');

const tokenDeployerJSON = require('../build/contracts/TokenDeployer.json');
const toposCoreJSON = require('../build/contracts/ToposCore.json');
const toposCoreProxyJSON = require('../build/contracts/ToposCoreProxy.json');

const CONST_ADDRESS_DEPLOYER_ADDR =
  '0x0000000000000000000000000000000000001110';

const main = async function (endpoint) {
  const provider = new ethers.providers.JsonRpcProvider(endpoint);
  const privateKey = process.env.PRIVATE_KEY;
  const tokenDeployerSalt = process.env.TOKEN_DEPLOYER_SALT;
  const toposCoreSalt = process.env.TOPOS_CORE_SALT;
  const toposCoreProxySalt = process.env.TOPOS_CORE_PROXY_SALT;

  if (!privateKey || ethers.utils.isHexString(privateKey, 32)) {
    console.error('ERROR: Please provide a valid private key! (PRIVATE_KEY)');
    return;
  }

  if (!tokenDeployerSalt) {
    console.error(
      'ERROR: Please provide a salt for TokenDeployer! (TOKEN_DEPLOYER_SALT)',
    );
    return;
  }

  if (!toposCoreSalt) {
    console.error(
      'ERROR: Please provide a salt for ToposCore! (TOKEN_DEPLOYER_SALT)',
    );
    return;
  }

  const wallet = new ethers.Wallet(process.env.PRIVATE_KEY, provider);

  console.info(`Verifying if TokenDeployer is already deployed...`);

  const existingTokenDeployerAddress = await predictContractAddress(
    wallet,
    tokenDeployerJSON,
    tokenDeployerSalt,
  );

  const tokenDeployerCode = await provider.getCode(
    existingTokenDeployerAddress,
  );

  if (tokenDeployerCode !== '0x') {
    console.info(`TokenDeployer is already deployed!`);
  } else {
    console.info(`Deploying TokenDeployer with constant address...`);

    const tokenDeployerAddress = await deployConstAddress(
      wallet,
      tokenDeployerJSON,
      tokenDeployerSalt,
    );

    console.info(
      `Successfully deployed TokenDeployer at ${tokenDeployerAddress}\n`,
    );
  }

  console.info(`\nVerifying if ToposCore is already deployed...`);

  const existingToposCoreAddress = await predictContractAddress(
    wallet,
    toposCoreJSON,
    toposCoreSalt,
    [
      existingTokenDeployerAddress || tokenDeployerAddress,
      '0x3100000000000000000000000000000000000000000000000000000000000000',
    ],
  );

  const toposCoreCode = await provider.getCode(existingToposCoreAddress);

  if (toposCoreCode !== '0x') {
    console.info(`ToposCore is already deployed!`);
  } else {
    console.info(`Deploying ToposCore...`);

    const toposCoreAddress = await deployConstAddress(
      wallet,
      toposCoreJSON,
      toposCoreSalt,
      [
        existingTokenDeployerAddress || tokenDeployerAddress,
        '0x3100000000000000000000000000000000000000000000000000000000000000',
      ],
      4_000_000,
    );

    console.info(`Successfully deployed ToposCore at ${toposCoreAddress}\n`);
  }

  console.info(`\nVerifying if ToposCoreProxy is already deployed...`);

  const params = ethers.utils.defaultAbiCoder.encode(
    ['address[]', 'uint256'],
    [[wallet.address], 1], // TODO: Use a different admin address than ToposDeployer
  );

  const existingToposCoreProxyAddress = await predictContractAddress(
    wallet,
    toposCoreProxyJSON,
    toposCoreProxySalt,
    [existingToposCoreAddress || toposCoreAddress, params],
  );

  const toposCoreProxyCode = await provider.getCode(
    existingToposCoreProxyAddress,
  );

  if (toposCoreProxyCode !== '0x') {
    console.info(`ToposCoreProxy is already deployed!`);
  } else {
    console.info(`Deploying ToposCoreProxy with constant address...`);

    const toposCoreProxyAddress = await deployConstAddress(
      wallet,
      toposCoreProxyJSON,
      toposCoreProxySalt,
      [existingToposCoreAddress || toposCoreAddress, params],
      4_000_000,
    );

    console.info(
      `Successfully deployed ToposCoreProxy at ${toposCoreProxyAddress}\n`,
    );
  }
};

const deployConstAddress = function (
  wallet,
  contractJson,
  salt,
  args,
  gasLimit = 0,
) {
  return axelarUtils
    .deployContractConstant(
      CONST_ADDRESS_DEPLOYER_ADDR,
      wallet,
      contractJson,
      salt,
      args,
      gasLimit === 0 ? null : gasLimit,
    )
    .then((contract) => contract.address)
    .catch((error) => {
      console.error(error);
      process.exit(1);
    });
};

const predictContractAddress = function (wallet, contractJson, salt, args) {
  return axelarUtils
    .predictContractConstant(
      CONST_ADDRESS_DEPLOYER_ADDR,
      wallet,
      contractJson,
      salt,
      args,
    )
    .catch((error) => {
      console.error(error);
      process.exit(1);
    });
};

const args = process.argv.slice(2);
main(...args);
