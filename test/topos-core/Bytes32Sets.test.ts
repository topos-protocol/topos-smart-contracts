import { Contract } from 'ethers'
import { ethers } from 'hardhat'
import { expect } from 'chai'

describe('Bytes32Sets', () => {
  let bytes32SetsTest: Contract

  const key1 = ethers.utils.formatBytes32String('key1')
  const key2 = ethers.utils.formatBytes32String('key2')

  beforeEach(async () => {
    const Bytes32SetsTest = await ethers.getContractFactory('Bytes32SetsTest')
    bytes32SetsTest = await Bytes32SetsTest.deploy()
    await bytes32SetsTest.deployed()
  })

  describe('insert', () => {
    it('reverts if the key is already in the set', async () => {
      await insertTestKey(key1)
      await expect(insertTestKey(key1)).to.be.revertedWith(
        'Bytes32Set: key already exists in the set.'
      )
    })

    it('inserts a key', async () => {
      await insertTestKey(key1)
      expect(await keyExists(key1)).to.be.true
    })
  })

  describe('remove', () => {
    it('reverts if the key is not in the set', async () => {
      await expect(removeTestKey(key1)).to.be.revertedWith(
        'Bytes32Set: key does not exist in the set.'
      )
    })

    it('removes a key', async () => {
      await insertTestKey(key1)
      await removeTestKey(key1)
      expect(await keyExists(key1)).to.be.false
    })

    it('removes the key before the last key', async () => {
      await insertTestKey(key1)
      await insertTestKey(key2)
      await removeTestKey(key1)
      expect(await keyExists(key1)).to.be.false
      expect(await keyExists(key2)).to.be.true
    })
  })

  describe('count', () => {
    it('returns the number of keys in the set', async () => {
      expect(await getCount()).to.equal(0)
      await insertTestKey(key1)
      expect(await getCount()).to.equal(1)
      await removeTestKey(key1)
      expect(await getCount()).to.equal(0)
    })
  })

  describe('exists', () => {
    it('returns true if the key exists in the set', async () => {
      expect(await keyExists(key1)).to.be.false
      await insertTestKey(key1)
      expect(await keyExists(key1)).to.be.true
    })
  })

  describe('keyAtIndex', () => {
    it('returns the key at the given index', async () => {
      await insertTestKey(key1)
      expect(await getKeyAtIndex(0)).to.equal(key1)
    })
  })

  async function insertTestKey(key: string) {
    await bytes32SetsTest.insert(key)
  }

  async function removeTestKey(key: string) {
    await bytes32SetsTest.remove(key)
  }

  async function getCount() {
    return await bytes32SetsTest.count()
  }

  async function keyExists(key: string) {
    return await bytes32SetsTest.exists(key)
  }

  async function getKeyAtIndex(index: number) {
    return await bytes32SetsTest.keyAtIndex(index)
  }
})