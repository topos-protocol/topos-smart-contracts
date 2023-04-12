import { Contract } from 'ethers'
import { ethers } from 'hardhat'
import { expect } from 'chai'

describe('TCENodeRegistrator', () => {
  let tceNodeRegistrator: Contract

  const peerId =
    '0x0000000000000000000000000000000000000000000000000000000000000001'

  beforeEach(async () => {
    const TCENodeRegistrator = await ethers.getContractFactory(
      'TCENodeRegistrator'
    )
    tceNodeRegistrator = await TCENodeRegistrator.deploy()
  })

  describe('registerTCENode', () => {
    it('reverts if the peerId is already registered', async () => {
      await registerTCENode(peerId)
      await expect(registerTCENode(peerId))
        .to.be.revertedWithCustomError(
          tceNodeRegistrator,
          'TCENodeAlreadyRegistered'
        )
        .withArgs(peerId)
    })

    it('registers a TCE node', async () => {
      await registerTCENode(peerId)
      const tceNode = await tceNodeRegistrator.tceNodes(peerId)
      expect(tceNode.peerId).to.equal(peerId)
      expect(tceNode.isPresent).to.equal(true)
    })

    it('emits a new TCE node registered event', async () => {
      await expect(registerTCENode(peerId))
        .to.emit(tceNodeRegistrator, 'NewTCENodeRegistered')
        .withArgs(peerId)
    })
  })

  describe('removeTCENode', () => {
    it('reverts if the peerId is not registered', async () => {
      await expect(removeTCENode(peerId))
        .to.be.revertedWithCustomError(
          tceNodeRegistrator,
          'TCENodeNotRegistered'
        )
        .withArgs(peerId)
    })

    it('emits a TCE node removed event', async () => {
      await registerTCENode(peerId)
      await expect(removeTCENode(peerId))
        .to.emit(tceNodeRegistrator, 'TCENodeRemoved')
        .withArgs(peerId)
    })
  })

  async function registerTCENode(peerId: string) {
    return await tceNodeRegistrator.registerTCENode(peerId)
  }

  async function removeTCENode(peerId: string) {
    return await tceNodeRegistrator.removeTCENode(peerId)
  }
})
