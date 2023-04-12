import { Contract } from 'ethers'
import { ethers } from 'hardhat'
import { expect } from 'chai'

describe('SubnetRegistrator', () => {
  let subnetRegistrator: Contract

  const endpoint = 'http://127.0.0.1'
  const logoURL = 'http://image-url.com'
  const subnetName = 'Test Subnet'
  const subnetId =
    '0x0000000000000000000000000000000000000000000000000000000000000001'
  const subnetCurrencySymbol = 'SUB'
  const chainId = 1

  beforeEach(async () => {
    const SubnetRegistrator = await ethers.getContractFactory(
      'SubnetRegistrator'
    )
    subnetRegistrator = await SubnetRegistrator.deploy()
  })

  describe('registerSubnet', () => {
    it('reverts if the subnet is already registered', async () => {
      await registerSubnet(
        endpoint,
        logoURL,
        subnetName,
        subnetId,
        subnetCurrencySymbol,
        chainId
      )
      await expect(
        registerSubnet(
          endpoint,
          logoURL,
          subnetName,
          subnetId,
          subnetCurrencySymbol,
          chainId
        )
      ).to.be.revertedWith('Bytes32Set: key already exists in the set.')
    })

    it('registers a subnet', async () => {
      await registerSubnet(
        endpoint,
        logoURL,
        subnetName,
        subnetId,
        subnetCurrencySymbol,
        chainId
      )
      const subnet = await subnetRegistrator.subnets(subnetId)
      expect(subnet.name).to.equal(subnetName)
      expect(subnet.currencySymbol).to.equal(subnetCurrencySymbol)
      expect(subnet.endpoint).to.equal(endpoint)
      expect(subnet.logoURL).to.equal(logoURL)
      expect(subnet.chainId).to.equal(chainId)
    })

    it('gets the subnet count', async () => {
      await registerSubnet(
        endpoint,
        logoURL,
        subnetName,
        subnetId,
        subnetCurrencySymbol,
        chainId
      )
      const count = await subnetRegistrator.getSubnetCount()
      expect(count).to.equal(1)
    })

    it('gets the subnet at a given index', async () => {
      await registerSubnet(
        endpoint,
        logoURL,
        subnetName,
        subnetId,
        subnetCurrencySymbol,
        chainId
      )
      const id = await subnetRegistrator.getSubnetIdAtIndex(0)
      expect(id).to.equal(subnetId)
    })

    it('checks if a subnet exists', async () => {
      await registerSubnet(
        endpoint,
        logoURL,
        subnetName,
        subnetId,
        subnetCurrencySymbol,
        chainId
      )
      const exists = await subnetRegistrator.subnetExists(subnetId)
      expect(exists).to.be.true
    })

    it('emits a new subnet registered event', async () => {
      await expect(
        registerSubnet(
          endpoint,
          logoURL,
          subnetName,
          subnetId,
          subnetCurrencySymbol,
          chainId
        )
      )
        .to.emit(subnetRegistrator, 'NewSubnetRegistered')
        .withArgs(subnetId)
    })
  })

  describe('removeSubnet', () => {
    it('reverts when removing a non-existent subnet', async () => {
      await expect(removeSubnet(subnetId)).to.be.revertedWith(
        'Bytes32Set: key does not exist in the set.'
      )
    })

    it('emit a subnet removed event', async () => {
      await registerSubnet(
        endpoint,
        logoURL,
        subnetName,
        subnetId,
        subnetCurrencySymbol,
        chainId
      )
      await expect(removeSubnet(subnetId))
        .to.emit(subnetRegistrator, 'SubnetRemoved')
        .withArgs(subnetId)
    })
  })

  async function registerSubnet(
    endpoint: string,
    logoURL: string,
    subnetName: string,
    subnetId: string,
    subnetCurrencySymbol: string,
    chainId: number
  ) {
    return await subnetRegistrator.registerSubnet(
      endpoint,
      logoURL,
      subnetName,
      subnetId,
      subnetCurrencySymbol,
      chainId
    )
  }

  async function removeSubnet(subnetId: string) {
    return await subnetRegistrator.removeSubnet(subnetId)
  }
})
