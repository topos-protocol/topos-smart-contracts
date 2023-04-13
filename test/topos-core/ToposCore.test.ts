import { ethers } from 'hardhat'
import { expect } from 'chai'
import * as cc from './shared/constants/certificates'
import * as tc from './shared/constants/tokens'
import * as txc from './shared/constants/transactions'
import * as testUtils from './shared/utils/toposCoreTest'

describe('ToposCore', () => {
  async function deployToposCoreFixture() {
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

    const ToposCoreProxy = await ethers.getContractFactory('ToposCoreProxy')
    const ToposCore = await ethers.getContractFactory('ToposCore')
    const ERC20 = await ethers.getContractFactory('ERC20')

    const toposCoreImplementation = await testUtils.deployNewToposCore()
    const toposCoreProxy = await ToposCoreProxy.deploy(
      toposCoreImplementation.address,
      setupParams
    )
    const toposCore = ToposCore.attach(toposCoreProxy.address)

    return { admin, defaultCert, defaultToken, ERC20, setupParams, toposCore }
  }

  describe('constructor', () => {
    it('reverts if the token deployer is the zero address', async () => {
      const ToposCore = await ethers.getContractFactory('ToposCore')
      await expect(ToposCore.deploy(ethers.constants.AddressZero)).to.be
        .reverted
    })
  })

  describe('pushCertificate', () => {
    it('reverts if the certificate is already stored', async () => {
      const { defaultCert, toposCore } = await deployToposCoreFixture()
      await toposCore.pushCertificate(defaultCert, cc.CERT_POS_1)
      await expect(
        toposCore.pushCertificate(defaultCert, cc.CERT_POS_1)
      ).to.be.revertedWith('Bytes32Set: key already exists in the set.')
    })

    it('gets the certificate count', async () => {
      const { defaultCert, toposCore } = await deployToposCoreFixture()
      await toposCore.pushCertificate(defaultCert, cc.CERT_POS_1)
      expect(await toposCore.getCertificateCount()).to.equal(1)
    })

    it('gets count for multiple certificates', async () => {
      const { defaultCert, toposCore } = await deployToposCoreFixture()
      var testCheckpoints = [
        [cc.CERT_ID_1, cc.CERT_POS_1, cc.SOURCE_SUBNET_ID_1],
        [cc.CERT_ID_2, cc.CERT_POS_2, cc.SOURCE_SUBNET_ID_2],
      ]

      for (const checkpoint of testCheckpoints) {
        const certificate = testUtils.encodeCertParam(
          cc.PREV_CERT_ID_0,
          checkpoint[2].toString(),
          cc.STATE_ROOT_MAX,
          cc.TX_ROOT_MAX,
          [cc.TARGET_SUBNET_ID_4],
          cc.VERIFIER,
          checkpoint[0].toString(),
          cc.DUMMY_STARK_PROOF,
          cc.DUMMY_SIGNATURE
        )
        await toposCore.pushCertificate(certificate, checkpoint[1])
      }
      expect(await toposCore.getCertificateCount()).to.equal(2)
    })

    it('gets the certificate at a given index', async () => {
      const { defaultCert, toposCore } = await deployToposCoreFixture()
      await toposCore.pushCertificate(defaultCert, cc.CERT_POS_1)
      const certificate = await toposCore.getCertIdAtIndex(0)
      expect(certificate).to.equal(cc.CERT_ID_1)
    })

    it('updates the source subnet set correctly', async () => {
      const { toposCore } = await deployToposCoreFixture()
      var testCheckpoints = [
        [cc.CERT_ID_1, cc.CERT_POS_1, cc.SOURCE_SUBNET_ID_1],
        [cc.CERT_ID_2, cc.CERT_POS_2, cc.SOURCE_SUBNET_ID_2],
        [cc.CERT_ID_3, cc.CERT_POS_3, cc.SOURCE_SUBNET_ID_3],
      ]

      for (const checkpoint of testCheckpoints) {
        const certificate = testUtils.encodeCertParam(
          cc.PREV_CERT_ID_0,
          checkpoint[2].toString(),
          cc.STATE_ROOT_MAX,
          cc.TX_ROOT_MAX,
          [cc.TARGET_SUBNET_ID_4],
          cc.VERIFIER,
          checkpoint[0].toString(),
          cc.DUMMY_STARK_PROOF,
          cc.DUMMY_SIGNATURE
        )
        await toposCore.pushCertificate(certificate, checkpoint[1])
      }

      const encodedCheckpoints = await toposCore.getCheckpoints()
      const checkpoints = encodedCheckpoints.map((checkpoint) => {
        return [checkpoint[0], checkpoint[1].toNumber(), checkpoint[2]]
      })
      testCheckpoints.map((innerArr1, i) =>
        innerArr1.map((item, j) => expect(item).to.equal(checkpoints[i][j]))
      )
      const updatedTestCheckpoint = [
        cc.CERT_ID_4,
        cc.CERT_POS_4,
        cc.SOURCE_SUBNET_ID_2,
      ]
      const updatedCertificate = testUtils.encodeCertParam(
        cc.PREV_CERT_ID_0,
        updatedTestCheckpoint[2].toString(),
        cc.STATE_ROOT_MAX,
        cc.TX_ROOT_MAX,
        [cc.TARGET_SUBNET_ID_4],
        cc.VERIFIER,
        updatedTestCheckpoint[0].toString(),
        cc.DUMMY_STARK_PROOF,
        cc.DUMMY_SIGNATURE
      )
      await toposCore.pushCertificate(
        updatedCertificate,
        updatedTestCheckpoint[1]
      )
      const updatedEncodedCheckpoints = await toposCore.getCheckpoints()
      const updatedCheckpoints = updatedEncodedCheckpoints.map((checkpoint) => {
        return [checkpoint[0], checkpoint[1].toNumber(), checkpoint[2]]
      })
      testCheckpoints[1] = updatedTestCheckpoint
      testCheckpoints.map((innerArr1, i) =>
        innerArr1.map((item, j) =>
          expect(item).to.equal(updatedCheckpoints[i][j])
        )
      )
    })

    it('emits a certificate stored event', async () => {
      const { defaultCert, toposCore } = await deployToposCoreFixture()
      const tx = await toposCore.pushCertificate(defaultCert, cc.CERT_POS_1)
      await expect(tx)
        .to.emit(toposCore, 'CertStored')
        .withArgs(cc.CERT_ID_1, cc.TX_ROOT_MAX)
    })
  })

  describe('deployToken', () => {
    it('gets the token count', async () => {
      const { defaultToken, toposCore } = await deployToposCoreFixture()
      await toposCore.deployToken(defaultToken)
      expect(await toposCore.getTokenCount()).to.equal(1)
    })

    it('gets count for multiple tokens', async () => {
      const { defaultToken, toposCore } = await deployToposCoreFixture()
      await toposCore.deployToken(defaultToken)
      const tokenTwo = testUtils.encodeTokenParam(
        tc.TOKEN_NAME,
        tc.TOKEN_SYMBOL_Y,
        tc.MINT_CAP_1_000_000,
        ethers.constants.AddressZero,
        tc.DAILY_MINT_LIMIT_100
      )
      await toposCore.deployToken(tokenTwo)
      expect(await toposCore.getTokenCount()).to.equal(2)
    })

    it('gets token by token key hash', async () => {
      const { defaultToken, toposCore } = await deployToposCoreFixture()
      const tx = await toposCore.deployToken(defaultToken)
      const { logs } = await tx.wait()
      const tokenAddress = logs[0]['address']
      const tokenKeyHash = await toposCore.getTokenKeyAtIndex(0)
      const token = await toposCore.tokens(tokenKeyHash)
      expect(token[0]).to.equal(tc.TOKEN_SYMBOL_X)
      expect(token[1]).to.equal(tokenAddress)
    })

    it('reverts if the token is already deployed', async () => {
      const { defaultToken, toposCore } = await deployToposCoreFixture()
      await toposCore.deployToken(defaultToken)
      await expect(toposCore.deployToken(defaultToken))
        .to.be.revertedWithCustomError(toposCore, 'TokenAlreadyExists')
        .withArgs(tc.TOKEN_SYMBOL_X)
      expect(await toposCore.getTokenCount()).to.equal(1)
    })

    it('emits a token deployed event', async () => {
      const { defaultToken, toposCore } = await deployToposCoreFixture()
      const tx = await toposCore.deployToken(defaultToken)
      const { logs } = await tx.wait()
      const tokenAddress = logs[0]['address']
      await expect(tx)
        .to.emit(toposCore, 'TokenDeployed')
        .withArgs(tc.TOKEN_SYMBOL_X, tokenAddress)
    })
  })

  describe('setTokenDailyMintLimits', () => {
    it('reverts if the token symbol length mismatch mint limit length', async () => {
      const { toposCore } = await deployToposCoreFixture()
      const symbols = ['ABC', 'XYZ']
      const mintLimits = [1]
      await expect(
        toposCore.setTokenDailyMintLimits(symbols, mintLimits)
      ).to.be.revertedWithCustomError(
        toposCore,
        'InvalidSetDailyMintLimitsParams'
      )
    })

    it('revert if the token symbol does not exist', async () => {
      const { toposCore } = await deployToposCoreFixture()
      const symbols = ['ABC']
      const mintLimits = [1]
      await expect(toposCore.setTokenDailyMintLimits(symbols, mintLimits))
        .to.be.revertedWithCustomError(toposCore, 'TokenDoesNotExist')
        .withArgs('ABC')
    })

    it('emits a token daily mint limits set event', async () => {
      const { defaultToken, toposCore } = await deployToposCoreFixture()
      await toposCore.deployToken(defaultToken)
      const symbols = [tc.TOKEN_SYMBOL_X]
      const mintLimits = [1]
      const tx = await toposCore.setTokenDailyMintLimits(symbols, mintLimits)
      await expect(tx)
        .to.emit(toposCore, 'TokenDailyMintLimitUpdated')
        .withArgs(tc.TOKEN_SYMBOL_X, 1)
    })
  })

  describe('proxy', () => {
    it('reverts if the ToposCore implementation contract is not present', async () => {
      const [admin] = await ethers.getSigners()
      const ToposCoreProxy = await ethers.getContractFactory('ToposCoreProxy')
      const setupParams = ethers.utils.defaultAbiCoder.encode(
        ['address[]', 'uint256'],
        [[admin.address], 1]
      )
      await expect(
        ToposCoreProxy.deploy(ethers.constants.AddressZero, setupParams)
      ).to.be.reverted
    })

    it('reverts if the admin threshold mismatch the length of the admin list', async () => {
      const [admin] = await ethers.getSigners()
      const toposCoreImplementation = await testUtils.deployNewToposCore()
      const setupParams = ethers.utils.defaultAbiCoder.encode(
        ['address[]', 'uint256'],
        [[admin.address], 2] // admin threshold is 2, but only one admin
      )
      const ToposCoreProxy = await ethers.getContractFactory('ToposCoreProxy')
      await expect(
        ToposCoreProxy.deploy(toposCoreImplementation.address, setupParams)
      ).to.be.reverted
    })

    it('reverts if the admin threshold is zero', async () => {
      const [admin] = await ethers.getSigners()
      const toposCoreImplementation = await testUtils.deployNewToposCore()
      const setupParams = ethers.utils.defaultAbiCoder.encode(
        ['address[]', 'uint256'],
        [[admin.address], 0] // admin threshold is 0
      )
      const ToposCoreProxy = await ethers.getContractFactory('ToposCoreProxy')
      await expect(
        ToposCoreProxy.deploy(toposCoreImplementation.address, setupParams)
      ).to.be.reverted
    })

    it('reverts if trying to add duplicate admins', async () => {
      const [admin] = await ethers.getSigners()
      const toposCoreImplementation = await testUtils.deployNewToposCore()
      const setupParams = ethers.utils.defaultAbiCoder.encode(
        ['address[]', 'uint256'],
        [[admin.address, admin.address], 1] // duplicate admin
      )
      const ToposCoreProxy = await ethers.getContractFactory('ToposCoreProxy')
      await expect(
        ToposCoreProxy.deploy(toposCoreImplementation.address, setupParams)
      ).to.be.reverted
    })

    it('reverts if the admin address is zero address', async () => {
      const toposCoreImplementation = await testUtils.deployNewToposCore()
      const setupParams = ethers.utils.defaultAbiCoder.encode(
        ['address[]', 'uint256'],
        [[ethers.constants.AddressZero], 1] // zero address
      )
      const ToposCoreProxy = await ethers.getContractFactory('ToposCoreProxy')
      await expect(
        ToposCoreProxy.deploy(toposCoreImplementation.address, setupParams)
      ).to.be.reverted
    })
  })

  describe('setup', () => {
    it('reverts if not called by the ToposCoreProxy contract', async () => {
      const { setupParams } = await deployToposCoreFixture()
      const toposCoreImplementation = await testUtils.deployNewToposCore()
      await expect(
        toposCoreImplementation.setup(setupParams)
      ).to.be.revertedWithCustomError(toposCoreImplementation, 'NotProxy')
    })
  })

  describe('executeAssetTransfer', () => {
    it('deploys a token with zero mint limit', async () => {
      const { ERC20, toposCore } = await deployToposCoreFixture()
      await toposCore.setNetworkSubnetId(cc.SOURCE_SUBNET_ID_2)
      const token = testUtils.encodeTokenParam(
        tc.TOKEN_NAME,
        tc.TOKEN_SYMBOL_X,
        tc.MINT_CAP_1_000_000,
        ethers.constants.AddressZero,
        0
      )
      const tx = await toposCore.deployToken(token)
      const { logs } = await tx.wait()
      const tokenAddress = logs[0]['address']
      const erc20 = ERC20.attach(tokenAddress)
      var certificate = testUtils.encodeCertParam(
        cc.PREV_CERT_ID_0,
        cc.SOURCE_SUBNET_ID_1,
        cc.STATE_ROOT_MAX,
        txc.NormalTransaction.TX_ROOT,
        [cc.SOURCE_SUBNET_ID_2],
        cc.VERIFIER,
        cc.CERT_ID_1,
        cc.DUMMY_STARK_PROOF,
        cc.DUMMY_SIGNATURE
      )
      await toposCore.pushCertificate(certificate, cc.CERT_POS_1)
      await expect(
        toposCore.executeAssetTransfer(
          txc.INDEX_OF_TX_DATA_33,
          txc.NormalTransaction.PROOF_BLOB,
          txc.NormalTransaction.TX_RAW,
          txc.NormalTransaction.TX_ROOT
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
      const { defaultToken, toposCore } = await deployToposCoreFixture()
      await toposCore.deployToken(defaultToken)
      await expect(
        toposCore.executeAssetTransfer(
          txc.OUT_OF_BOUNDS_INDEX_OF_DATA_295, // index of tx data is out of range
          txc.NormalTransaction.PROOF_BLOB,
          txc.NormalTransaction.TX_RAW,
          txc.NormalTransaction.TX_ROOT
        )
      ).to.be.revertedWithCustomError(toposCore, 'IllegalMemoryAccess')
    })

    it('reverts if the certificate is not present', async () => {
      const { defaultToken, toposCore } = await deployToposCoreFixture()
      await toposCore.deployToken(defaultToken)
      await expect(
        toposCore.executeAssetTransfer(
          txc.INDEX_OF_TX_DATA_33,
          txc.NormalTransaction.PROOF_BLOB,
          txc.NormalTransaction.TX_RAW,
          txc.NormalTransaction.TX_ROOT
        )
      ).to.be.revertedWithCustomError(toposCore, 'CertNotPresent')
    })

    it('reverts if the merkle proof is invalid', async () => {
      const { defaultToken, toposCore } = await deployToposCoreFixture()
      await toposCore.setNetworkSubnetId(cc.SOURCE_SUBNET_ID_2)
      await toposCore.deployToken(defaultToken)
      var certificate = testUtils.encodeCertParam(
        cc.PREV_CERT_ID_0,
        cc.SOURCE_SUBNET_ID_1,
        cc.STATE_ROOT_MAX,
        txc.NormalTransaction.TX_ROOT,
        [cc.SOURCE_SUBNET_ID_2],
        cc.VERIFIER,
        cc.CERT_ID_1,
        cc.DUMMY_STARK_PROOF,
        cc.DUMMY_SIGNATURE
      )
      await toposCore.pushCertificate(certificate, cc.CERT_POS_1)
      await expect(
        toposCore.executeAssetTransfer(
          txc.INDEX_OF_TX_DATA_33,
          txc.NormalTransaction.FAKE_PROOF_BLOB,
          txc.NormalTransaction.TX_RAW,
          txc.NormalTransaction.TX_ROOT
        )
      ).to.be.reverted
    })

    it('reverts if the target subnet id is mismatched', async () => {
      const { defaultToken, toposCore } = await deployToposCoreFixture()
      await toposCore.setNetworkSubnetId(cc.SOURCE_SUBNET_ID_1)
      await toposCore.deployToken(defaultToken)
      var certificate = testUtils.encodeCertParam(
        cc.PREV_CERT_ID_0,
        cc.SOURCE_SUBNET_ID_1,
        cc.STATE_ROOT_MAX,
        txc.NormalTransaction.TX_ROOT,
        [cc.SOURCE_SUBNET_ID_1], // target subnet id in the hardcoded tx = SOURCE_SUBNET_ID_2
        cc.VERIFIER,
        cc.CERT_ID_1,
        cc.DUMMY_STARK_PROOF,
        cc.DUMMY_SIGNATURE
      )
      await toposCore.pushCertificate(certificate, cc.CERT_POS_1)
      await expect(
        toposCore.executeAssetTransfer(
          txc.INDEX_OF_TX_DATA_33,
          txc.NormalTransaction.PROOF_BLOB,
          txc.NormalTransaction.TX_RAW,
          txc.NormalTransaction.TX_ROOT
        )
      ).to.be.revertedWithCustomError(toposCore, 'InvalidSubnetId')
    })

    it('reverts if the transaction is already executed', async () => {
      const { defaultToken, toposCore } = await deployToposCoreFixture()
      await toposCore.setNetworkSubnetId(cc.SOURCE_SUBNET_ID_2)
      await toposCore.deployToken(defaultToken)
      var certificate = testUtils.encodeCertParam(
        cc.PREV_CERT_ID_0,
        cc.SOURCE_SUBNET_ID_1,
        cc.STATE_ROOT_MAX,
        txc.NormalTransaction.TX_ROOT,
        [cc.SOURCE_SUBNET_ID_2],
        cc.VERIFIER,
        cc.CERT_ID_1,
        cc.DUMMY_STARK_PROOF,
        cc.DUMMY_SIGNATURE
      )
      await toposCore.pushCertificate(certificate, cc.CERT_POS_1)
      await toposCore.executeAssetTransfer(
        txc.INDEX_OF_TX_DATA_33,
        txc.NormalTransaction.PROOF_BLOB,
        txc.NormalTransaction.TX_RAW,
        txc.NormalTransaction.TX_ROOT
      )
      await expect(
        toposCore.executeAssetTransfer(
          txc.INDEX_OF_TX_DATA_33,
          txc.NormalTransaction.PROOF_BLOB,
          txc.NormalTransaction.TX_RAW,
          txc.NormalTransaction.TX_ROOT
        )
      ).to.be.revertedWithCustomError(toposCore, 'TransferAlreadyExecuted')
    })

    it('reverts if the token is not deployed yet', async () => {
      const { toposCore } = await deployToposCoreFixture()
      await toposCore.setNetworkSubnetId(cc.SOURCE_SUBNET_ID_2)
      var certificate = testUtils.encodeCertParam(
        cc.PREV_CERT_ID_0,
        cc.SOURCE_SUBNET_ID_1,
        cc.STATE_ROOT_MAX,
        txc.NormalTransaction.TX_ROOT,
        [cc.SOURCE_SUBNET_ID_2],
        cc.VERIFIER,
        cc.CERT_ID_1,
        cc.DUMMY_STARK_PROOF,
        cc.DUMMY_SIGNATURE
      )
      await toposCore.pushCertificate(certificate, cc.CERT_POS_1)
      await expect(
        toposCore.executeAssetTransfer(
          txc.INDEX_OF_TX_DATA_33,
          txc.NormalTransaction.PROOF_BLOB,
          txc.NormalTransaction.TX_RAW,
          txc.NormalTransaction.TX_ROOT
        )
      ).to.be.revertedWithCustomError(toposCore, 'TokenDoesNotExist')
    })

    it('reverts if the daily mint limit is exceeded', async () => {
      const { defaultToken, toposCore } = await deployToposCoreFixture()
      await toposCore.setNetworkSubnetId(cc.SOURCE_SUBNET_ID_2)
      await toposCore.deployToken(defaultToken)
      var certificate = testUtils.encodeCertParam(
        cc.PREV_CERT_ID_0,
        cc.SOURCE_SUBNET_ID_1,
        cc.STATE_ROOT_MAX,
        txc.MintExceedTransaction.TX_ROOT,
        [cc.SOURCE_SUBNET_ID_2],
        cc.VERIFIER,
        cc.CERT_ID_1,
        cc.DUMMY_STARK_PROOF,
        cc.DUMMY_SIGNATURE
      )
      await toposCore.pushCertificate(certificate, cc.CERT_POS_1)
      await expect(
        toposCore.executeAssetTransfer(
          txc.INDEX_OF_TX_DATA_33,
          txc.MintExceedTransaction.PROOF_BLOB,
          txc.MintExceedTransaction.TX_RAW,
          txc.MintExceedTransaction.TX_ROOT
        )
      ).to.be.revertedWithCustomError(toposCore, 'ExceedDailyMintLimit')
    })

    it('emits the Transfer success event', async () => {
      const { ERC20, defaultToken, toposCore } = await deployToposCoreFixture()
      await toposCore.setNetworkSubnetId(cc.SOURCE_SUBNET_ID_2)
      const tx = await toposCore.deployToken(defaultToken)
      const { logs } = await tx.wait()
      const tokenAddress = logs[0]['address']
      const erc20 = ERC20.attach(tokenAddress)
      var certificate = testUtils.encodeCertParam(
        cc.PREV_CERT_ID_0,
        cc.SOURCE_SUBNET_ID_1,
        cc.STATE_ROOT_MAX,
        txc.NormalTransaction.TX_ROOT,
        [cc.SOURCE_SUBNET_ID_2],
        cc.VERIFIER,
        cc.CERT_ID_1,
        cc.DUMMY_STARK_PROOF,
        cc.DUMMY_SIGNATURE
      )
      await toposCore.pushCertificate(certificate, cc.CERT_POS_1)
      await expect(
        toposCore.executeAssetTransfer(
          txc.INDEX_OF_TX_DATA_33,
          txc.NormalTransaction.PROOF_BLOB,
          txc.NormalTransaction.TX_RAW,
          txc.NormalTransaction.TX_ROOT
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
      const { toposCore } = await deployToposCoreFixture()
      await expect(
        toposCore.sendToken(
          cc.TARGET_SUBNET_ID_4,
          tc.RECIPIENT_ADDRESS,
          tc.TOKEN_SYMBOL_X,
          tc.SEND_AMOUNT_50
        )
      )
        .to.be.revertedWithCustomError(toposCore, 'TokenDoesNotExist')
        .withArgs(tc.TOKEN_SYMBOL_X)
    })

    it('reverts if the send amount is zero', async () => {
      const { defaultToken, toposCore } = await deployToposCoreFixture()
      await toposCore.deployToken(defaultToken)
      await expect(
        toposCore.sendToken(
          cc.TARGET_SUBNET_ID_4,
          tc.RECIPIENT_ADDRESS,
          tc.TOKEN_SYMBOL_X,
          0
        )
      ).to.be.revertedWithCustomError(toposCore, 'InvalidAmount')
    })

    it('reverts if the send amount is not approved', async () => {
      const { defaultToken, toposCore } = await deployToposCoreFixture()
      await toposCore.deployToken(defaultToken)
      await expect(
        toposCore.sendToken(
          cc.TARGET_SUBNET_ID_4,
          tc.RECIPIENT_ADDRESS,
          tc.TOKEN_SYMBOL_X,
          tc.SEND_AMOUNT_50
        )
      )
        .to.be.revertedWithCustomError(toposCore, 'BurnFailed')
        .withArgs(tc.TOKEN_SYMBOL_X)
    })

    it('emits a token sent event', async () => {
      const { admin, ERC20, defaultToken, toposCore } =
        await deployToposCoreFixture()
      await toposCore.setNetworkSubnetId(cc.SOURCE_SUBNET_ID_2)
      const tx = await toposCore.deployToken(defaultToken)
      const { logs } = await tx.wait()
      const tokenAddress = logs[0]['address']
      const erc20 = ERC20.attach(tokenAddress)
      await toposCore.giveToken(
        tc.TOKEN_SYMBOL_X,
        admin.address,
        tc.SEND_AMOUNT_50
      )
      await erc20.approve(toposCore.address, tc.SEND_AMOUNT_50)
      await expect(
        toposCore.sendToken(
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
        .to.emit(toposCore, 'TokenSent')
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

  describe('upgrade', () => {
    it('reverts if the code hash does not match', async () => {
      const { admin, toposCore } = await deployToposCoreFixture()
      const toposCoreImplementation = await testUtils.deployNewToposCore()
      const setupParams = ethers.utils.defaultAbiCoder.encode(
        ['address[]', 'uint256'],
        [[admin.address], 1]
      )
      await expect(
        toposCore.upgrade(
          toposCoreImplementation.address,
          '0x0000000000000000000000000000000000000000000000000000000000000000',
          setupParams
        )
      ).to.be.revertedWithCustomError(toposCore, 'InvalidCodeHash')
    })

    it('emits an upgraded event', async () => {
      const { admin, toposCore } = await deployToposCoreFixture()
      const toposCoreImplementation = await testUtils.deployNewToposCore()
      expect(await toposCore.implementation()).to.not.equal(
        toposCoreImplementation.address
      )

      const CodeHash = await ethers.getContractFactory('CodeHash')
      const codeHash = await CodeHash.deploy()
      const implementationCodeHash = await codeHash.getCodeHash(
        toposCoreImplementation.address
      )
      const setupParams = ethers.utils.defaultAbiCoder.encode(
        ['address[]', 'uint256'],
        [[admin.address], 1]
      )

      await expect(
        toposCore.upgrade(
          toposCoreImplementation.address,
          implementationCodeHash,
          setupParams
        )
      )
        .to.emit(toposCore, 'Upgraded')
        .withArgs(toposCoreImplementation.address)
      expect(await toposCore.implementation()).to.equal(
        toposCoreImplementation.address
      )
    })
  })
})
