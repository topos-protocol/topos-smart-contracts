import { ethers } from 'hardhat'
import { expect } from 'chai'
import { loadFixture } from '@nomicfoundation/hardhat-network-helpers'
import * as cc from './shared/constants/certificates'
import * as tc from './shared/constants/tokens'
import * as txc from './shared/constants/transactions'
import * as testUtils from './shared/utils/common'

describe('ToposMessaging', () => {
  async function deployToposMessagingFixture() {
    const [admin] = await ethers.getSigners()
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
      tc.MINT_CAP_1_000_000,
      ethers.constants.AddressZero,
      tc.DAILY_MINT_LIMIT_100
    )
    const setupParams = ethers.utils.defaultAbiCoder.encode(
      ['address[]', 'uint256'],
      [[admin.address], 1]
    )

    const TokenDeployer = await ethers.getContractFactory('TokenDeployer')
    const ToposCore = await ethers.getContractFactory('ToposCore')
    const ToposCoreProxy = await ethers.getContractFactory('ToposCoreProxy')
    const ERC20 = await ethers.getContractFactory('ERC20')
    const ToposMessaging = await ethers.getContractFactory('ToposMessaging')

    const tokenDeployer = await TokenDeployer.deploy()
    const toposCoreImplementation = await ToposCore.deploy()
    const toposCoreProxy = await ToposCoreProxy.deploy(
      toposCoreImplementation.address,
      setupParams
    )
    const toposCore = ToposCore.attach(toposCoreProxy.address)
    const toposMessaging = await ToposMessaging.deploy(
      tokenDeployer.address,
      toposCore.address
    )

    return {
      admin,
      defaultCert,
      defaultToken,
      ERC20,
      toposCore,
      toposMessaging,
    }
  }

  describe('deployToken', () => {
    it('gets the token count', async () => {
      const { defaultToken, toposMessaging } = await loadFixture(
        deployToposMessagingFixture
      )
      await toposMessaging.deployToken(defaultToken)
      expect(await toposMessaging.getTokenCount()).to.equal(1)
    })

    it('gets count for multiple tokens', async () => {
      const { defaultToken, toposMessaging } = await loadFixture(
        deployToposMessagingFixture
      )
      await toposMessaging.deployToken(defaultToken)
      const tokenTwo = testUtils.encodeTokenParam(
        tc.TOKEN_NAME,
        tc.TOKEN_SYMBOL_Y,
        tc.MINT_CAP_1_000_000,
        ethers.constants.AddressZero,
        tc.DAILY_MINT_LIMIT_100
      )
      await toposMessaging.deployToken(tokenTwo)
      expect(await toposMessaging.getTokenCount()).to.equal(2)
    })

    it('gets token by token key hash', async () => {
      const { defaultToken, toposMessaging } = await loadFixture(
        deployToposMessagingFixture
      )
      const tx = await toposMessaging.deployToken(defaultToken)
      const { logs } = await tx.wait()
      const tokenAddress = logs[0]['address']
      const tokenKeyHash = await toposMessaging.getTokenKeyAtIndex(0)
      const token = await toposMessaging.tokens(tokenKeyHash)
      expect(token[0]).to.equal(tc.TOKEN_SYMBOL_X)
      expect(token[1]).to.equal(tokenAddress)
    })

    it('reverts if the token is already deployed', async () => {
      const { defaultToken, toposMessaging } = await loadFixture(
        deployToposMessagingFixture
      )
      await toposMessaging.deployToken(defaultToken)
      await expect(toposMessaging.deployToken(defaultToken))
        .to.be.revertedWithCustomError(toposMessaging, 'TokenAlreadyExists')
        .withArgs(tc.TOKEN_SYMBOL_X)
      expect(await toposMessaging.getTokenCount()).to.equal(1)
    })

    it('emits a token deployed event', async () => {
      const { defaultToken, toposMessaging } = await loadFixture(
        deployToposMessagingFixture
      )
      const tx = await toposMessaging.deployToken(defaultToken)
      const { logs } = await tx.wait()
      const tokenAddress = logs[0]['address']
      await expect(tx)
        .to.emit(toposMessaging, 'TokenDeployed')
        .withArgs(tc.TOKEN_SYMBOL_X, tokenAddress)
    })
  })

  //   describe('setTokenDailyMintLimits', () => {
  //     it('reverts if the token symbol length mismatch mint limit length', async () => {
  //       const { toposMessaging } = await loadFixture(deployToposMessagingFixture)
  //       const symbols = ['ABC', 'XYZ']
  //       const mintLimits = [1]
  //       await expect(
  //         toposMessaging.setTokenDailyMintLimits(symbols, mintLimits)
  //       ).to.be.revertedWithCustomError(
  //         toposMessaging,
  //         'InvalidSetDailyMintLimitsParams'
  //       )
  //     })

  //     it('revert if the token symbol does not exist', async () => {
  //       const { toposMessaging } = await loadFixture(deployToposMessagingFixture)
  //       const symbols = ['ABC']
  //       const mintLimits = [1]
  //       await expect(toposMessaging.setTokenDailyMintLimits(symbols, mintLimits))
  //         .to.be.revertedWithCustomError(toposMessaging, 'TokenDoesNotExist')
  //         .withArgs('ABC')
  //     })

  //     it('emits a token daily mint limits set event', async () => {
  //       const { defaultToken, toposMessaging } = await loadFixture(
  //         deployToposMessagingFixture
  //       )
  //       await toposMessaging.deployToken(defaultToken)
  //       const symbols = [tc.TOKEN_SYMBOL_X]
  //       const mintLimits = [1]
  //       const tx = await toposMessaging.setTokenDailyMintLimits(symbols, mintLimits)
  //       await expect(tx)
  //         .to.emit(toposMessaging, 'TokenDailyMintLimitUpdated')
  //         .withArgs(tc.TOKEN_SYMBOL_X, 1)
  //     })
  //   })

  describe('executeAssetTransfer', () => {
    it('deploys a token with zero mint limit', async () => {
      const { ERC20, toposCore, toposMessaging } = await loadFixture(
        deployToposMessagingFixture
      )
      await toposCore.setNetworkSubnetId(cc.SOURCE_SUBNET_ID_2)
      const token = testUtils.encodeTokenParam(
        tc.TOKEN_NAME,
        tc.TOKEN_SYMBOL_X,
        tc.MINT_CAP_1_000_000,
        ethers.constants.AddressZero,
        0
      )
      const tx = await toposMessaging.deployToken(token)
      const { logs } = await tx.wait()
      const tokenAddress = logs[0]['address']
      const erc20 = ERC20.attach(tokenAddress)
      const certificate = testUtils.encodeCertParam(
        cc.PREV_CERT_ID_0,
        cc.SOURCE_SUBNET_ID_1,
        cc.STATE_ROOT_MAX,
        txc.NORMAL_TRANSACTION.txRoot,
        [cc.SOURCE_SUBNET_ID_2],
        cc.VERIFIER,
        cc.CERT_ID_1,
        cc.DUMMY_STARK_PROOF,
        cc.DUMMY_SIGNATURE
      )
      await toposCore.pushCertificate(certificate, cc.CERT_POS_1)
      await expect(
        toposMessaging.executeAssetTransfer(
          txc.INDEX_OF_TX_DATA_33,
          txc.NORMAL_TRANSACTION.proofBlob,
          txc.NORMAL_TRANSACTION.txRaw,
          txc.NORMAL_TRANSACTION.txRoot
        )
      )
        .to.emit(erc20, 'Transfer')
        .withArgs(
          ethers.constants.AddressZero,
          tc.RECIPIENT_ADDRESS, // default address in the hardcoded tx
          tc.SEND_AMOUNT_50 // default amount sent in the hardcoded tx
        )
    })

    it('reverts if the index of tx data is out of range', async () => {
      const { defaultToken, toposMessaging } = await loadFixture(
        deployToposMessagingFixture
      )
      await toposMessaging.deployToken(defaultToken)
      await expect(
        toposMessaging.executeAssetTransfer(
          txc.OUT_OF_BOUNDS_INDEX_OF_DATA_295, // index of tx data is out of range
          txc.NORMAL_TRANSACTION.proofBlob,
          txc.NORMAL_TRANSACTION.txRaw,
          txc.NORMAL_TRANSACTION.txRoot
        )
      ).to.be.revertedWithCustomError(toposMessaging, 'IllegalMemoryAccess')
    })

    it('reverts if the certificate is not present', async () => {
      const { defaultToken, toposMessaging } = await loadFixture(
        deployToposMessagingFixture
      )
      await toposMessaging.deployToken(defaultToken)
      await expect(
        toposMessaging.executeAssetTransfer(
          txc.INDEX_OF_TX_DATA_33,
          txc.NORMAL_TRANSACTION.proofBlob,
          txc.NORMAL_TRANSACTION.txRaw,
          txc.NORMAL_TRANSACTION.txRoot
        )
      ).to.be.revertedWithCustomError(toposMessaging, 'CertNotPresent')
    })

    it('reverts if the merkle proof is invalid', async () => {
      const { defaultToken, toposCore, toposMessaging } = await loadFixture(
        deployToposMessagingFixture
      )
      await toposCore.setNetworkSubnetId(cc.SOURCE_SUBNET_ID_2)
      await toposMessaging.deployToken(defaultToken)
      const certificate = testUtils.encodeCertParam(
        cc.PREV_CERT_ID_0,
        cc.SOURCE_SUBNET_ID_1,
        cc.STATE_ROOT_MAX,
        txc.NORMAL_TRANSACTION.txRoot,
        [cc.SOURCE_SUBNET_ID_2],
        cc.VERIFIER,
        cc.CERT_ID_1,
        cc.DUMMY_STARK_PROOF,
        cc.DUMMY_SIGNATURE
      )
      await toposCore.pushCertificate(certificate, cc.CERT_POS_1)
      const fakeProofBlob = txc.NORMAL_TRANSACTION.optionalData
      await expect(
        toposMessaging.executeAssetTransfer(
          txc.INDEX_OF_TX_DATA_33,
          fakeProofBlob ? fakeProofBlob[0] : '0x',
          txc.NORMAL_TRANSACTION.txRaw,
          txc.NORMAL_TRANSACTION.txRoot
        )
      ).to.be.reverted
    })

    it('reverts if the target subnet id is mismatched', async () => {
      const { defaultToken, toposCore, toposMessaging } = await loadFixture(
        deployToposMessagingFixture
      )
      await toposCore.setNetworkSubnetId(cc.SOURCE_SUBNET_ID_1)
      await toposMessaging.deployToken(defaultToken)
      const certificate = testUtils.encodeCertParam(
        cc.PREV_CERT_ID_0,
        cc.SOURCE_SUBNET_ID_1,
        cc.STATE_ROOT_MAX,
        txc.NORMAL_TRANSACTION.txRoot,
        [cc.SOURCE_SUBNET_ID_1], // target subnet id in the hardcoded tx = SOURCE_SUBNET_ID_2
        cc.VERIFIER,
        cc.CERT_ID_1,
        cc.DUMMY_STARK_PROOF,
        cc.DUMMY_SIGNATURE
      )
      await toposCore.pushCertificate(certificate, cc.CERT_POS_1)
      await expect(
        toposMessaging.executeAssetTransfer(
          txc.INDEX_OF_TX_DATA_33,
          txc.NORMAL_TRANSACTION.proofBlob,
          txc.NORMAL_TRANSACTION.txRaw,
          txc.NORMAL_TRANSACTION.txRoot
        )
      ).to.be.revertedWithCustomError(toposMessaging, 'InvalidSubnetId')
    })

    it('reverts if the transaction is already executed', async () => {
      const { defaultToken, toposCore, toposMessaging } = await loadFixture(
        deployToposMessagingFixture
      )
      await toposCore.setNetworkSubnetId(cc.SOURCE_SUBNET_ID_2)
      await toposMessaging.deployToken(defaultToken)
      const certificate = testUtils.encodeCertParam(
        cc.PREV_CERT_ID_0,
        cc.SOURCE_SUBNET_ID_1,
        cc.STATE_ROOT_MAX,
        txc.NORMAL_TRANSACTION.txRoot,
        [cc.SOURCE_SUBNET_ID_2],
        cc.VERIFIER,
        cc.CERT_ID_1,
        cc.DUMMY_STARK_PROOF,
        cc.DUMMY_SIGNATURE
      )
      await toposCore.pushCertificate(certificate, cc.CERT_POS_1)
      await toposMessaging.executeAssetTransfer(
        txc.INDEX_OF_TX_DATA_33,
        txc.NORMAL_TRANSACTION.proofBlob,
        txc.NORMAL_TRANSACTION.txRaw,
        txc.NORMAL_TRANSACTION.txRoot
      )
      await expect(
        toposMessaging.executeAssetTransfer(
          txc.INDEX_OF_TX_DATA_33,
          txc.NORMAL_TRANSACTION.proofBlob,
          txc.NORMAL_TRANSACTION.txRaw,
          txc.NORMAL_TRANSACTION.txRoot
        )
      ).to.be.revertedWithCustomError(toposMessaging, 'TransferAlreadyExecuted')
    })

    it('reverts if the token is not deployed yet', async () => {
      const { toposCore, toposMessaging } = await loadFixture(
        deployToposMessagingFixture
      )
      await toposCore.setNetworkSubnetId(cc.SOURCE_SUBNET_ID_2)
      const certificate = testUtils.encodeCertParam(
        cc.PREV_CERT_ID_0,
        cc.SOURCE_SUBNET_ID_1,
        cc.STATE_ROOT_MAX,
        txc.NORMAL_TRANSACTION.txRoot,
        [cc.SOURCE_SUBNET_ID_2],
        cc.VERIFIER,
        cc.CERT_ID_1,
        cc.DUMMY_STARK_PROOF,
        cc.DUMMY_SIGNATURE
      )
      await toposCore.pushCertificate(certificate, cc.CERT_POS_1)
      await expect(
        toposMessaging.executeAssetTransfer(
          txc.INDEX_OF_TX_DATA_33,
          txc.NORMAL_TRANSACTION.proofBlob,
          txc.NORMAL_TRANSACTION.txRaw,
          txc.NORMAL_TRANSACTION.txRoot
        )
      ).to.be.revertedWithCustomError(toposMessaging, 'TokenDoesNotExist')
    })

    it('reverts if the daily mint limit is exceeded', async () => {
      const { defaultToken, toposCore, toposMessaging } = await loadFixture(
        deployToposMessagingFixture
      )
      await toposCore.setNetworkSubnetId(cc.SOURCE_SUBNET_ID_2)
      await toposMessaging.deployToken(defaultToken)
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
        toposMessaging.executeAssetTransfer(
          txc.INDEX_OF_TX_DATA_33,
          txc.MINT_EXCEED_TRANSACTION.proofBlob,
          txc.MINT_EXCEED_TRANSACTION.txRaw,
          txc.MINT_EXCEED_TRANSACTION.txRoot
        )
      ).to.be.revertedWithCustomError(toposMessaging, 'ExceedDailyMintLimit')
    })

    it('reverts if trying to mint for zero address', async () => {
      const { defaultToken, toposCore, toposMessaging } = await loadFixture(
        deployToposMessagingFixture
      )
      await toposCore.setNetworkSubnetId(cc.SOURCE_SUBNET_ID_2)
      await toposMessaging.deployToken(defaultToken)
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
        toposMessaging.executeAssetTransfer(
          txc.INDEX_OF_TX_DATA_33,
          txc.ZERO_ADDRESS_TRANSACTION.proofBlob,
          txc.ZERO_ADDRESS_TRANSACTION.txRaw,
          txc.ZERO_ADDRESS_TRANSACTION.txRoot
        )
      ).to.be.revertedWith('ERC20: mint to the zero address')
    })

    it('emits the Transfer success event', async () => {
      const { ERC20, defaultToken, toposCore, toposMessaging } =
        await loadFixture(deployToposMessagingFixture)
      await toposCore.setNetworkSubnetId(cc.SOURCE_SUBNET_ID_2)
      const tx = await toposMessaging.deployToken(defaultToken)
      const { logs } = await tx.wait()
      const tokenAddress = logs[0]['address']
      const erc20 = ERC20.attach(tokenAddress)
      const certificate = testUtils.encodeCertParam(
        cc.PREV_CERT_ID_0,
        cc.SOURCE_SUBNET_ID_1,
        cc.STATE_ROOT_MAX,
        txc.NORMAL_TRANSACTION.txRoot,
        [cc.SOURCE_SUBNET_ID_2],
        cc.VERIFIER,
        cc.CERT_ID_1,
        cc.DUMMY_STARK_PROOF,
        cc.DUMMY_SIGNATURE
      )
      await toposCore.pushCertificate(certificate, cc.CERT_POS_1)
      await expect(
        toposMessaging.executeAssetTransfer(
          txc.INDEX_OF_TX_DATA_33,
          txc.NORMAL_TRANSACTION.proofBlob,
          txc.NORMAL_TRANSACTION.txRaw,
          txc.NORMAL_TRANSACTION.txRoot
        )
      )
        .to.emit(erc20, 'Transfer')
        .withArgs(
          ethers.constants.AddressZero,
          tc.RECIPIENT_ADDRESS, // default address in the hardcoded tx
          tc.SEND_AMOUNT_50 // default amount sent in the hardcoded tx
        )
    })
  })

  describe('sendToken', () => {
    it('reverts if the token is not deployed yet', async () => {
      const { toposMessaging } = await loadFixture(deployToposMessagingFixture)
      await expect(
        toposMessaging.sendToken(
          cc.TARGET_SUBNET_ID_4,
          tc.RECIPIENT_ADDRESS,
          tc.TOKEN_SYMBOL_X,
          tc.SEND_AMOUNT_50
        )
      )
        .to.be.revertedWithCustomError(toposMessaging, 'TokenDoesNotExist')
        .withArgs(tc.TOKEN_SYMBOL_X)
    })

    it('reverts if the send amount is zero', async () => {
      const { defaultToken, toposMessaging } = await loadFixture(
        deployToposMessagingFixture
      )
      await toposMessaging.deployToken(defaultToken)
      await expect(
        toposMessaging.sendToken(
          cc.TARGET_SUBNET_ID_4,
          tc.RECIPIENT_ADDRESS,
          tc.TOKEN_SYMBOL_X,
          0
        )
      ).to.be.revertedWithCustomError(toposMessaging, 'InvalidAmount')
    })

    it('reverts if the send amount is not approved', async () => {
      const { defaultToken, toposMessaging } = await loadFixture(
        deployToposMessagingFixture
      )
      await toposMessaging.deployToken(defaultToken)
      await expect(
        toposMessaging.sendToken(
          cc.TARGET_SUBNET_ID_4,
          tc.RECIPIENT_ADDRESS,
          tc.TOKEN_SYMBOL_X,
          tc.SEND_AMOUNT_50
        )
      )
        .to.be.revertedWithCustomError(toposMessaging, 'BurnFailed')
        .withArgs(tc.TOKEN_SYMBOL_X)
    })

    it('emits a token sent event', async () => {
      const { admin, ERC20, defaultToken, toposCore, toposMessaging } =
        await loadFixture(deployToposMessagingFixture)
      await toposCore.setNetworkSubnetId(cc.SOURCE_SUBNET_ID_2)
      const tx = await toposMessaging.deployToken(defaultToken)
      const { logs } = await tx.wait()
      const tokenAddress = logs[0]['address']
      const erc20 = ERC20.attach(tokenAddress)
      await toposMessaging.giveToken(
        tc.TOKEN_SYMBOL_X,
        admin.address,
        tc.SEND_AMOUNT_50
      )
      await erc20.approve(toposMessaging.address, tc.SEND_AMOUNT_50)
      await expect(
        toposMessaging.sendToken(
          cc.TARGET_SUBNET_ID_4,
          tc.RECIPIENT_ADDRESS,
          tc.TOKEN_SYMBOL_X,
          tc.SEND_AMOUNT_50
        )
      )
        .to.emit(erc20, 'Transfer')
        .withArgs(
          admin.address,
          ethers.constants.AddressZero,
          tc.SEND_AMOUNT_50
        )
        .to.emit(toposMessaging, 'TokenSent')
        .withArgs(
          admin.address,
          cc.SOURCE_SUBNET_ID_2,
          cc.TARGET_SUBNET_ID_4,
          tc.RECIPIENT_ADDRESS,
          tc.TOKEN_SYMBOL_X,
          tc.SEND_AMOUNT_50
        )
    })
  })
})
