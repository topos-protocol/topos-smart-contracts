import { Contract } from 'ethers'
import { deployContractConstant } from '../../scripts/const-addr-deployer'
import { ethers, network } from 'hardhat'
import { expect } from 'chai'
import { getMptProof } from './shared/utils/mpt_proof'
import { loadFixture } from '@nomicfoundation/hardhat-network-helpers'
import { JsonRpcProvider } from '@ethersproject/providers'
import { SignerWithAddress } from '@nomiclabs/hardhat-ethers/signers'

import * as cc from './shared/constants/certificates'
import * as tc from './shared/constants/tokens'
import * as txc from './shared/constants/transactions'
import * as testUtils from './shared/utils/common'

import * as tokenDeployerJSON from '../../artifacts/contracts/topos-core/TokenDeployer.sol/TokenDeployer.json'
import { ERC20__factory, ERC20Messaging } from '../../typechain-types'

describe('ToposMessaging', () => {
  async function deployERC20MessagingFixture() {
    await network.provider.send('hardhat_reset')
    const defaultAddressMnemonic =
      'test test test test test test test test test test test junk'
    const tokenDeployerSalt = ethers.utils.keccak256(
      Buffer.from('TokenDeployer')
    )
    const [admin, receiver] = await ethers.getSigners()
    let wallet = ethers.Wallet.fromMnemonic(defaultAddressMnemonic)
    wallet = wallet.connect(ethers.provider)
    const defaultCert = testUtils.encodeCertParam(
      cc.PREV_CERT_ID_0,
      cc.SOURCE_SUBNET_ID_1,
      cc.STATE_ROOT_MAX,
      cc.TX_ROOT_MAX,
      [cc.TARGET_SUBNET_ID_4, cc.TARGET_SUBNET_ID_5],
      cc.VERIFIER,
      cc.CERT_ID_1,
      cc.DUMMY_STARK_PROOF,
      cc.DUMMY_SIGNATURE
    )
    const defaultToken = testUtils.encodeTokenParam(
      tc.TOKEN_NAME,
      tc.TOKEN_SYMBOL_X,
      tc.MINT_CAP_100_000_000,
      ethers.constants.AddressZero,
      tc.DAILY_MINT_LIMIT_100,
      tc.INITIAL_SUPPLY_10_000_000
    )
    const setupParams = ethers.utils.defaultAbiCoder.encode(
      ['address[]', 'uint256'],
      [[admin.address], 1]
    )

    const ConstAddressDeployer = await ethers.getContractFactory(
      'ConstAddressDeployer'
    )
    const ERC20 = await ethers.getContractFactory('ERC20')
    const TokenDeployer = await ethers.getContractFactory('TokenDeployer')
    const ToposCore = await ethers.getContractFactory('ToposCore')
    const ToposCoreProxy = await ethers.getContractFactory('ToposCoreProxy')
    const ERC20Messaging = await ethers.getContractFactory('ERC20Messaging')

    const constAddressDeployer = await ConstAddressDeployer.deploy()

    const tokenDeployerAddress = await deployContractConstant(
      wallet,
      tokenDeployerJSON,
      tokenDeployerSalt,
      [],
      4_000_000,
      constAddressDeployer.address
    )
    const tokenDeployer = TokenDeployer.attach(tokenDeployerAddress.address)

    const toposCoreImplementation = await ToposCore.deploy()
    const toposCoreProxy = await ToposCoreProxy.deploy(
      toposCoreImplementation.address,
      setupParams
    )
    const toposCore = ToposCore.attach(toposCoreProxy.address)

    const erc20Messaging = await ERC20Messaging.deploy(
      tokenDeployer.address,
      toposCore.address
    )
    const erc20MessagingContract = new ethers.Contract(
      erc20Messaging.address,
      ERC20Messaging.interface,
      admin
    )

    return {
      admin,
      receiver,
      defaultCert,
      defaultToken,
      ERC20,
      toposCore,
      erc20Messaging,
      erc20MessagingContract,
    }
  }

  describe('deployToken', () => {
    it('gets the token count', async () => {
      const { defaultToken, erc20Messaging } = await loadFixture(
        deployERC20MessagingFixture
      )
      await erc20Messaging.deployToken(defaultToken)
      expect(await erc20Messaging.getTokenCount()).to.equal(1)
    })

    it('gets count for multiple tokens', async () => {
      const { defaultToken, erc20Messaging } = await loadFixture(
        deployERC20MessagingFixture
      )
      await erc20Messaging.deployToken(defaultToken)
      const tokenTwo = testUtils.encodeTokenParam(
        tc.TOKEN_NAME,
        tc.TOKEN_SYMBOL_Y,
        tc.MINT_CAP_100_000_000,
        ethers.constants.AddressZero,
        tc.DAILY_MINT_LIMIT_100,
        tc.INITIAL_SUPPLY_10_000_000
      )
      await erc20Messaging.deployToken(tokenTwo)
      expect(await erc20Messaging.getTokenCount()).to.equal(2)
    })

    it('gets token by token key hash', async () => {
      const { defaultToken, erc20Messaging } = await loadFixture(
        deployERC20MessagingFixture
      )
      const tx = await erc20Messaging.deployToken(defaultToken)
      const txReceipt = await tx.wait()
      const logs = txReceipt.events?.find((e) => e.event === 'TokenDeployed')
      const tokenAddress = logs?.args?.tokenAddress
      const tokenKeyHash = await erc20Messaging.getTokenKeyAtIndex(0)
      const token = await erc20Messaging.tokens(tokenKeyHash)
      expect(token[0]).to.equal(tc.TOKEN_SYMBOL_X)
      expect(token[1]).to.equal(tokenAddress)
    })

    it('reverts if a deployer deploys a token with the same symbol twice', async () => {
      const { defaultToken, erc20Messaging } = await loadFixture(
        deployERC20MessagingFixture
      )
      await erc20Messaging.deployToken(defaultToken)
      await expect(
        erc20Messaging.deployToken(defaultToken)
      ).to.be.revertedWithCustomError(erc20Messaging, 'TokenDeployFailed')
      expect(await erc20Messaging.getTokenCount()).to.equal(1)
    })

    it('reverts if the token is already deployed', async () => {
      const { defaultToken, erc20Messaging } = await loadFixture(
        deployERC20MessagingFixture
      )
      const tx = await erc20Messaging.deployToken(defaultToken)
      const txReceipt = await tx.wait()
      const logs = txReceipt.events?.find((e) => e.event === 'TokenDeployed')
      const tokenAddress = logs?.args?.tokenAddress
      const token = testUtils.encodeTokenParam(
        tc.TOKEN_NAME,
        tc.TOKEN_SYMBOL_X,
        tc.MINT_CAP_100_000_000,
        tokenAddress,
        tc.DAILY_MINT_LIMIT_100,
        tc.INITIAL_SUPPLY_10_000_000
      )
      await expect(
        erc20Messaging.deployToken(token)
      ).to.be.revertedWithCustomError(erc20Messaging, 'TokenAlreadyExists')
    })

    it('reverts if the token is an external token', async () => {
      const [extToken] = await ethers.getSigners()
      const { erc20Messaging } = await loadFixture(deployERC20MessagingFixture)
      const token = testUtils.encodeTokenParam(
        tc.TOKEN_NAME,
        tc.TOKEN_SYMBOL_X,
        tc.MINT_CAP_100_000_000,
        extToken.address,
        tc.DAILY_MINT_LIMIT_100,
        tc.INITIAL_SUPPLY_10_000_000
      )
      await expect(
        erc20Messaging.deployToken(token)
      ).to.be.revertedWithCustomError(erc20Messaging, 'UnsupportedTokenType')
      expect(await erc20Messaging.getTokenCount()).to.equal(0)
    })

    it('allows two separate deployers to deploy tokens with same symbol', async () => {
      const [deployerOne, deployerTwo] = await ethers.getSigners()
      const { defaultToken, erc20Messaging } = await loadFixture(
        deployERC20MessagingFixture
      )
      const erc20MessagingOne = erc20Messaging.connect(deployerOne)
      const txOne = await erc20MessagingOne.deployToken(defaultToken)
      const { logs: logsOne } = await txOne.wait()
      const tokenAddressOne = logsOne[0]['address']
      await expect(txOne)
        .to.emit(erc20Messaging, 'TokenDeployed')
        .withArgs(tc.TOKEN_SYMBOL_X, tokenAddressOne)

      const erc20MessagingTwo = erc20Messaging.connect(deployerTwo)
      const txTwo = await erc20MessagingTwo.deployToken(defaultToken)
      const { logs: logsTwo } = await txTwo.wait()
      const tokenAddressTwo = logsTwo[0]['address']
      await expect(txTwo)
        .to.emit(erc20Messaging, 'TokenDeployed')
        .withArgs(tc.TOKEN_SYMBOL_X, tokenAddressTwo)
      expect(tokenAddressOne).to.not.equal(tokenAddressTwo)
    })

    it('emits a token deployed event', async () => {
      const { defaultToken, erc20Messaging } = await loadFixture(
        deployERC20MessagingFixture
      )
      const tx = await erc20Messaging.deployToken(defaultToken)
      const txReceipt = await tx.wait()
      const logs = txReceipt.events?.find((e) => e.event === 'TokenDeployed')
      const tokenAddress = logs?.args?.tokenAddress
      await expect(tx)
        .to.emit(erc20Messaging, 'TokenDeployed')
        .withArgs(tc.TOKEN_SYMBOL_X, tokenAddress)
    })
  })

  describe('execute', () => {
    it('deploys a token with zero mint limit', async () => {
      const {
        admin,
        receiver,
        ERC20,
        toposCore,
        erc20Messaging,
        erc20MessagingContract,
      } = await loadFixture(deployERC20MessagingFixture)
      await toposCore.setNetworkSubnetId(cc.SOURCE_SUBNET_ID_2)
      const token = testUtils.encodeTokenParam(
        tc.TOKEN_NAME,
        tc.TOKEN_SYMBOL_X,
        tc.MINT_CAP_100_000_000,
        ethers.constants.AddressZero,
        0,
        tc.INITIAL_SUPPLY_10_000_000
      )
      const tx = await erc20Messaging.deployToken(token)
      const txReceipt = await tx.wait()
      const logs = txReceipt.events?.find((e) => e.event === 'TokenDeployed')
      const tokenAddress = logs?.args?.tokenAddress
      const erc20 = ERC20.attach(tokenAddress)
      await erc20.approve(erc20Messaging.address, tc.SEND_AMOUNT_50)

      const sendToken = await sendTokenTx(
        erc20MessagingContract,
        ethers.provider,
        receiver.address,
        admin,
        cc.SOURCE_SUBNET_ID_2,
        tokenAddress
      )

      const { indexOfTxData, proofBlob, transactionsRoot, txRaw } =
        await getMptProof(sendToken, ethers.provider)

      const certificate = testUtils.encodeCertParam(
        cc.PREV_CERT_ID_0,
        cc.SOURCE_SUBNET_ID_1,
        cc.STATE_ROOT_MAX,
        transactionsRoot,
        [cc.SOURCE_SUBNET_ID_2],
        cc.VERIFIER,
        cc.CERT_ID_1,
        cc.DUMMY_STARK_PROOF,
        cc.DUMMY_SIGNATURE
      )
      await toposCore.pushCertificate(certificate, cc.CERT_POS_1)
      await expect(
        erc20Messaging.execute(
          indexOfTxData,
          proofBlob,
          txRaw,
          transactionsRoot
        )
      )
        .to.emit(erc20, 'Transfer')
        .withArgs(
          ethers.constants.AddressZero,
          receiver.address,
          tc.SEND_AMOUNT_50
        )
    })

    it('reverts if the index of tx data is out of range', async () => {
      const {
        admin,
        receiver,
        defaultToken,
        ERC20,
        erc20Messaging,
        erc20MessagingContract,
      } = await loadFixture(deployERC20MessagingFixture)
      const { indexOfTxData, proofBlob, transactionsRoot, txRaw } =
        await deployDefaultToken(
          admin,
          receiver,
          ERC20,
          defaultToken,
          erc20Messaging,
          erc20MessagingContract
        )

      const outOfBoundsMax = 300
      await expect(
        erc20Messaging.execute(
          indexOfTxData + outOfBoundsMax,
          proofBlob,
          txRaw,
          transactionsRoot
        )
      ).to.be.revertedWithCustomError(erc20Messaging, 'IllegalMemoryAccess')
    })

    it('reverts if the certificate is not present', async () => {
      const {
        admin,
        receiver,
        defaultToken,
        ERC20,
        erc20Messaging,
        erc20MessagingContract,
      } = await loadFixture(deployERC20MessagingFixture)
      const { indexOfTxData, proofBlob, transactionsRoot, txRaw } =
        await deployDefaultToken(
          admin,
          receiver,
          ERC20,
          defaultToken,
          erc20Messaging,
          erc20MessagingContract
        )

      await expect(
        erc20Messaging.execute(
          indexOfTxData,
          proofBlob,
          txRaw,
          transactionsRoot
        )
      ).to.be.revertedWithCustomError(erc20Messaging, 'CertNotPresent')
    })

    it('reverts if the merkle proof is invalid', async () => {
      const {
        admin,
        receiver,
        defaultToken,
        ERC20,
        toposCore,
        erc20Messaging,
        erc20MessagingContract,
      } = await loadFixture(deployERC20MessagingFixture)
      const { indexOfTxData, transactionsRoot, txRaw } =
        await deployDefaultToken(
          admin,
          receiver,
          ERC20,
          defaultToken,
          erc20Messaging,
          erc20MessagingContract
        )

      await toposCore.setNetworkSubnetId(cc.SOURCE_SUBNET_ID_2)
      const certificate = testUtils.encodeCertParam(
        cc.PREV_CERT_ID_0,
        cc.SOURCE_SUBNET_ID_1,
        cc.STATE_ROOT_MAX,
        transactionsRoot,
        [cc.SOURCE_SUBNET_ID_2],
        cc.VERIFIER,
        cc.CERT_ID_1,
        cc.DUMMY_STARK_PROOF,
        cc.DUMMY_SIGNATURE
      )
      await toposCore.pushCertificate(certificate, cc.CERT_POS_1)
      const fakeProofBlob = '0x01'
      await expect(
        erc20Messaging.execute(
          indexOfTxData,
          fakeProofBlob,
          txRaw,
          transactionsRoot
        )
      ).to.be.reverted
    })

    it('reverts if the target subnet id is mismatched', async () => {
      const {
        admin,
        receiver,
        defaultToken,
        ERC20,
        toposCore,
        erc20Messaging,
        erc20MessagingContract,
      } = await loadFixture(deployERC20MessagingFixture)
      const { indexOfTxData, proofBlob, transactionsRoot, txRaw } =
        await deployDefaultToken(
          admin,
          receiver,
          ERC20,
          defaultToken,
          erc20Messaging,
          erc20MessagingContract
        )

      await toposCore.setNetworkSubnetId(cc.SOURCE_SUBNET_ID_1) // target subnet id = SOURCE_SUBNET_ID_2
      const certificate = testUtils.encodeCertParam(
        cc.PREV_CERT_ID_0,
        cc.SOURCE_SUBNET_ID_1,
        cc.STATE_ROOT_MAX,
        transactionsRoot,
        [cc.SOURCE_SUBNET_ID_2],
        cc.VERIFIER,
        cc.CERT_ID_1,
        cc.DUMMY_STARK_PROOF,
        cc.DUMMY_SIGNATURE
      )
      await toposCore.pushCertificate(certificate, cc.CERT_POS_1)
      await expect(
        erc20Messaging.execute(
          indexOfTxData,
          proofBlob,
          txRaw,
          transactionsRoot
        )
      ).to.be.revertedWithCustomError(erc20Messaging, 'InvalidSubnetId')
    })

    it('reverts if the transaction is already executed', async () => {
      const {
        admin,
        receiver,
        defaultToken,
        ERC20,
        toposCore,
        erc20Messaging,
        erc20MessagingContract,
      } = await loadFixture(deployERC20MessagingFixture)
      const { indexOfTxData, proofBlob, transactionsRoot, txRaw } =
        await deployDefaultToken(
          admin,
          receiver,
          ERC20,
          defaultToken,
          erc20Messaging,
          erc20MessagingContract
        )

      await toposCore.setNetworkSubnetId(cc.SOURCE_SUBNET_ID_2)
      const certificate = testUtils.encodeCertParam(
        cc.PREV_CERT_ID_0,
        cc.SOURCE_SUBNET_ID_1,
        cc.STATE_ROOT_MAX,
        transactionsRoot,
        [cc.SOURCE_SUBNET_ID_2],
        cc.VERIFIER,
        cc.CERT_ID_1,
        cc.DUMMY_STARK_PROOF,
        cc.DUMMY_SIGNATURE
      )
      await toposCore.pushCertificate(certificate, cc.CERT_POS_1)
      await erc20Messaging.execute(
        indexOfTxData,
        proofBlob,
        txRaw,
        transactionsRoot
      )
      await expect(
        erc20Messaging.execute(
          indexOfTxData,
          proofBlob,
          txRaw,
          transactionsRoot
        )
      ).to.be.revertedWithCustomError(
        erc20Messaging,
        'TransactionAlreadyExecuted'
      )
    })

    it('reverts if the token is not deployed yet', async () => {
      const { toposCore, erc20Messaging } = await loadFixture(
        deployERC20MessagingFixture
      )
      await toposCore.setNetworkSubnetId(cc.SOURCE_SUBNET_ID_2)
      const certificate = testUtils.encodeCertParam(
        cc.PREV_CERT_ID_0,
        cc.SOURCE_SUBNET_ID_1,
        cc.STATE_ROOT_MAX,
        txc.UNKNOWN_TOKEN_TRANSACTION.txRoot,
        [cc.SOURCE_SUBNET_ID_2],
        cc.VERIFIER,
        cc.CERT_ID_1,
        cc.DUMMY_STARK_PROOF,
        cc.DUMMY_SIGNATURE
      )
      await toposCore.pushCertificate(certificate, cc.CERT_POS_1)
      await expect(
        erc20Messaging.execute(
          txc.INDEX_OF_TX_DATA_36,
          txc.UNKNOWN_TOKEN_TRANSACTION.proofBlob,
          txc.UNKNOWN_TOKEN_TRANSACTION.txRaw,
          txc.UNKNOWN_TOKEN_TRANSACTION.txRoot
        )
      ).to.be.revertedWithCustomError(erc20Messaging, 'TokenDoesNotExist')
    })

    it('reverts if the daily mint limit is exceeded', async () => {
      const { defaultToken, toposCore, erc20Messaging } = await loadFixture(
        deployERC20MessagingFixture
      )
      await toposCore.setNetworkSubnetId(cc.SOURCE_SUBNET_ID_2)
      await erc20Messaging.deployToken(defaultToken)
      const certificate = testUtils.encodeCertParam(
        cc.PREV_CERT_ID_0,
        cc.SOURCE_SUBNET_ID_1,
        cc.STATE_ROOT_MAX,
        txc.MINT_EXCEED_TRANSACTION.txRoot,
        [cc.SOURCE_SUBNET_ID_2],
        cc.VERIFIER,
        cc.CERT_ID_1,
        cc.DUMMY_STARK_PROOF,
        cc.DUMMY_SIGNATURE
      )
      await toposCore.pushCertificate(certificate, cc.CERT_POS_1)
      await expect(
        erc20Messaging.execute(
          txc.INDEX_OF_TX_DATA_36,
          txc.MINT_EXCEED_TRANSACTION.proofBlob,
          txc.MINT_EXCEED_TRANSACTION.txRaw,
          txc.MINT_EXCEED_TRANSACTION.txRoot
        )
      ).to.be.revertedWithCustomError(erc20Messaging, 'ExceedDailyMintLimit')
    })

    it('reverts if trying to mint for zero address', async () => {
      const { defaultToken, toposCore, erc20Messaging } = await loadFixture(
        deployERC20MessagingFixture
      )
      await toposCore.setNetworkSubnetId(cc.SOURCE_SUBNET_ID_2)
      await erc20Messaging.deployToken(defaultToken)
      const certificate = testUtils.encodeCertParam(
        cc.PREV_CERT_ID_0,
        cc.SOURCE_SUBNET_ID_1,
        cc.STATE_ROOT_MAX,
        txc.ZERO_ADDRESS_TRANSACTION.txRoot,
        [cc.SOURCE_SUBNET_ID_2],
        cc.VERIFIER,
        cc.CERT_ID_1,
        cc.DUMMY_STARK_PROOF,
        cc.DUMMY_SIGNATURE
      )
      await toposCore.pushCertificate(certificate, cc.CERT_POS_1)
      await expect(
        erc20Messaging.execute(
          txc.INDEX_OF_TX_DATA_36,
          txc.ZERO_ADDRESS_TRANSACTION.proofBlob,
          txc.ZERO_ADDRESS_TRANSACTION.txRaw,
          txc.ZERO_ADDRESS_TRANSACTION.txRoot
        )
      ).to.be.revertedWith('ERC20: mint to the zero address')
    })

    it('emits the Transfer success event', async () => {
      const {
        admin,
        receiver,
        defaultToken,
        ERC20,
        toposCore,
        erc20Messaging,
        erc20MessagingContract,
      } = await loadFixture(deployERC20MessagingFixture)
      const { erc20, indexOfTxData, proofBlob, transactionsRoot, txRaw } =
        await deployDefaultToken(
          admin,
          receiver,
          ERC20,
          defaultToken,
          erc20Messaging,
          erc20MessagingContract
        )
      await toposCore.setNetworkSubnetId(cc.SOURCE_SUBNET_ID_2)
      const certificate = testUtils.encodeCertParam(
        cc.PREV_CERT_ID_0,
        cc.SOURCE_SUBNET_ID_1,
        cc.STATE_ROOT_MAX,
        transactionsRoot,
        [cc.SOURCE_SUBNET_ID_2],
        cc.VERIFIER,
        cc.CERT_ID_1,
        cc.DUMMY_STARK_PROOF,
        cc.DUMMY_SIGNATURE
      )
      await toposCore.pushCertificate(certificate, cc.CERT_POS_1)
      await expect(
        erc20Messaging.execute(
          indexOfTxData,
          proofBlob,
          txRaw,
          transactionsRoot
        )
      )
        .to.emit(erc20, 'Transfer')
        .withArgs(
          ethers.constants.AddressZero,
          receiver.address,
          tc.SEND_AMOUNT_50
        )
      await expect(erc20.balanceOf(receiver.address)).to.eventually.equal(
        tc.SEND_AMOUNT_50
      )
    })
  })

  describe('sendToken', () => {
    it('reverts if the token is not deployed yet', async () => {
      const [token] = await ethers.getSigners()
      const { erc20Messaging } = await loadFixture(deployERC20MessagingFixture)
      await expect(
        erc20Messaging.sendToken(
          cc.TARGET_SUBNET_ID_4,
          tc.RECIPIENT_ADDRESS,
          token.address,
          tc.SEND_AMOUNT_50
        )
      )
        .to.be.revertedWithCustomError(erc20Messaging, 'TokenDoesNotExist')
        .withArgs(token.address)
    })

    it('reverts if the send amount is zero', async () => {
      const { defaultToken, erc20Messaging } = await loadFixture(
        deployERC20MessagingFixture
      )
      const tx = await erc20Messaging.deployToken(defaultToken)
      const txReceipt = await tx.wait()
      const logs = txReceipt.events?.find((e) => e.event === 'TokenDeployed')
      const tokenAddress = logs?.args?.tokenAddress
      await expect(
        erc20Messaging.sendToken(
          cc.TARGET_SUBNET_ID_4,
          tc.RECIPIENT_ADDRESS,
          tokenAddress,
          0
        )
      ).to.be.revertedWithCustomError(erc20Messaging, 'InvalidAmount')
    })

    it('reverts if the send amount is not approved', async () => {
      const { defaultToken, erc20Messaging } = await loadFixture(
        deployERC20MessagingFixture
      )

      const tx = await erc20Messaging.deployToken(defaultToken)
      const txReceipt = await tx.wait()
      const logs = txReceipt.events?.find((e) => e.event === 'TokenDeployed')
      const tokenAddress = logs?.args?.tokenAddress
      await expect(
        erc20Messaging.sendToken(
          cc.TARGET_SUBNET_ID_4,
          tc.RECIPIENT_ADDRESS,
          tokenAddress,
          tc.SEND_AMOUNT_50
        )
      )
        .to.be.revertedWithCustomError(erc20Messaging, 'BurnFailed')
        .withArgs(tokenAddress)
    })

    it('emits a token sent event', async () => {
      const { admin, ERC20, defaultToken, toposCore, erc20Messaging } =
        await loadFixture(deployERC20MessagingFixture)
      await toposCore.setNetworkSubnetId(cc.SOURCE_SUBNET_ID_2)
      const tx = await erc20Messaging.deployToken(defaultToken)
      const txReceipt = await tx.wait()
      const logs = txReceipt.events?.find((e) => e.event === 'TokenDeployed')
      const tokenAddress = logs?.args?.tokenAddress
      const erc20 = ERC20.attach(tokenAddress)
      await erc20.approve(erc20Messaging.address, tc.SEND_AMOUNT_50)
      await expect(
        erc20Messaging.sendToken(
          cc.TARGET_SUBNET_ID_4,
          tc.RECIPIENT_ADDRESS,
          tokenAddress,
          tc.SEND_AMOUNT_50
        )
      )
        .to.emit(erc20, 'Transfer')
        .withArgs(
          admin.address,
          ethers.constants.AddressZero,
          tc.SEND_AMOUNT_50
        )
        .to.emit(toposCore, 'CrossSubnetMessageSent')
        .withArgs(cc.TARGET_SUBNET_ID_4)
    })
  })

  async function deployDefaultToken(
    admin: SignerWithAddress,
    receiver: SignerWithAddress,
    ERC20: ERC20__factory,
    defaultToken: string,
    erc20Messaging: ERC20Messaging,
    erc20MessagingContract: Contract
  ) {
    const tx = await erc20Messaging.deployToken(defaultToken)
    const txReceipt = await tx.wait()
    const logs = txReceipt.events?.find((e) => e.event === 'TokenDeployed')
    const tokenAddress = logs?.args?.tokenAddress
    const erc20 = ERC20.attach(tokenAddress)
    await erc20.approve(erc20Messaging.address, tc.SEND_AMOUNT_50)

    const sendToken = await sendTokenTx(
      erc20MessagingContract,
      ethers.provider,
      receiver.address,
      admin,
      cc.SOURCE_SUBNET_ID_2,
      tokenAddress
    )

    const { indexOfTxData, proofBlob, transactionsRoot, txRaw } =
      await getMptProof(sendToken, ethers.provider)
    return { erc20, indexOfTxData, proofBlob, transactionsRoot, txRaw }
  }

  async function sendTokenTx(
    contractInstance: Contract,
    provider: JsonRpcProvider,
    receiver: string,
    signer: SignerWithAddress,
    targetSubnetId: string,
    tokenAddress: string
  ) {
    const estimatedGasLimit = await contractInstance.estimateGas.sendToken(
      targetSubnetId,
      receiver,
      tokenAddress,
      tc.SEND_AMOUNT_50,
      { gasLimit: 4_000_000 }
    )
    const TxUnsigned = await contractInstance.populateTransaction.sendToken(
      targetSubnetId,
      receiver,
      tokenAddress,
      tc.SEND_AMOUNT_50,
      { gasLimit: 4_000_000 }
    )
    TxUnsigned.chainId = 31337 // Hardcoded chainId for Hardhat local testing
    TxUnsigned.gasLimit = estimatedGasLimit
    const address = signer.address
    const nonce = await provider.getTransactionCount(address)
    TxUnsigned.nonce = nonce
    TxUnsigned.gasPrice = await provider.getGasPrice()

    const submittedTx = await signer.sendTransaction(TxUnsigned)
    const receipt = await submittedTx.wait()
    if (receipt.status === 0) {
      throw new Error(
        `Send Token Tx is reverted with Tx hash : ${submittedTx.hash}`
      )
    }
    return submittedTx
  }
})