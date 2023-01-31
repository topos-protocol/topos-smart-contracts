const ethers = require('ethers');
const { MerkleTree } = require('merkletreejs');
const keccak256 = require('keccak256');

const merkleProofVerifyJSON = require('../build/contracts/MerkleProofVerify.json');

const ERROR_MISSING_ARGS = 'Missing required arguments';
const ERROR_PRIVATE_KEY_NOT_FOUND = 'Please provide a valid private key! (PRIVATE_KEY)';
const ERROR_TX_NOT_FOUND = 'Tx not found';

async function main(endpoint, leaf) {
    console.info('Getting tx inclusion proof...');
    const privateKey = process.env.PRIVATE_KEY;
    if (!privateKey || ethers.utils.isHexString(privateKey, 32)) {
        console.error(ERROR_PRIVATE_KEY_NOT_FOUND);
        return;
    }
    const provider = new ethers.providers.JsonRpcProvider(endpoint);
    const wallet = new ethers.Wallet(privateKey, provider);
    const targetTx = await provider.getTransaction(leaf);
    if (!targetTx) {
        console.error(ERROR_TX_NOT_FOUND);
        throw new Error(ERROR_TX_NOT_FOUND);
    }
    const rpcBlock = await provider.getBlock(targetTx.blockHash, true);

    const leaves = rpcBlock.transactions;
    const tree = new MerkleTree(leaves, keccak256, { sort: true });
    const root = tree.getRoot().toString('hex');
    const proof = tree.getProof(leaf)
    const hex_proof = tree.getHexProof(leaf);

    console.info(`leaf: ${leaf}\n`);
    console.info(`leaf index: ${parseInt(targetTx.transactionIndex, 16)}\n`);
    console.info(`leaves: ${leaves}\n`);
    console.info(`proof: ${hex_proof}\n`);
    console.log(`JavaScript Check - Transaction Included: ${tree.verify(proof, leaf, root)}`);

    console.info(`Deploying MerkleProofVerify...`);
    const merkleProofVerifyFactory = new ethers.ContractFactory(
        merkleProofVerifyJSON.abi,
        merkleProofVerifyJSON.bytecode,
        wallet,
    );
    const merkleProofVerify = await merkleProofVerifyFactory
        .deploy()
        .then(async (contract) => {
            await contract.deployTransaction.wait();
            return contract;
        });

    tx_result = await merkleProofVerify.verifyProof(hex_proof, '0x' + root, leaf);
    console.info(`MerkleProofVerify.sol Check - Transaction Included: ${tx_result}`);
}

const args = process.argv.slice(2);

if (args.length < 2) {
    console.error(ERROR_MISSING_ARGS);
    process.exit(1);
}

main(args[0], args[1]).catch(error => {
    console.error(error);
    process.exit(1);
});
