import { Contract, Wallet } from 'ethers'
import { ethers } from 'hardhat'
import { expect } from 'chai'

describe('SubnetRegistrator', () => {
  let subnetRegistrator: Contract

  const httpEndpoint = 'http://127.0.0.1'
  const wsEndpoint = 'ws://127.0.0.1'
  const logoURL = 'http://image-url.com'
  const subnetName = 'Test Subnet'
  const subnetId = ethers.utils.formatBytes32String('subnetId')
  const subnetCurrencySymbol = 'SUB'
  const chainId = 1

  async function deploySubnetRegistratorFixture() {
    const [admin, nonAdmin, toposDeployer] = await ethers.getSigners()
    const SubnetRegistrator = await ethers.getContractFactory(
      'SubnetRegistrator'
    )
    subnetRegistrator = await SubnetRegistrator.connect(toposDeployer).deploy()
    await subnetRegistrator.deployed()
    await subnetRegistrator.initialize(admin.address)
    return {
      admin,
      nonAdmin,
      subnetRegistrator,
      toposDeployer,
    }
  }

  describe('registerSubnet', () => {
    it('reverts if non-admin tries to register a subnet', async () => {
      const { nonAdmin, subnetRegistrator } =
        await deploySubnetRegistratorFixture()
      await expect(
        subnetRegistrator
          .connect(nonAdmin)
          .registerSubnet(
            httpEndpoint,
            wsEndpoint,
            logoURL,
            subnetName,
            subnetId,
            subnetCurrencySymbol,
            chainId
          )
      ).to.be.revertedWith('Ownable: caller is not the owner')
    })

    it('reverts if the subnet is already registered', async () => {
      const { admin, subnetRegistrator } =
        await deploySubnetRegistratorFixture()
      await registerSubnet(
        httpEndpoint,
        wsEndpoint,
        logoURL,
        subnetName,
        subnetId,
        subnetCurrencySymbol,
        chainId,
        subnetRegistrator,
        admin
      )
      await expect(
        registerSubnet(
          httpEndpoint,
          wsEndpoint,
          logoURL,
          subnetName,
          subnetId,
          subnetCurrencySymbol,
          chainId,
          subnetRegistrator,
          admin
        )
      ).to.be.revertedWith('Bytes32Set: key already exists in the set.')
    })

    it('registers a subnet', async () => {
      const { admin, subnetRegistrator } =
        await deploySubnetRegistratorFixture()
      await registerSubnet(
        httpEndpoint,
        wsEndpoint,
        logoURL,
        subnetName,
        subnetId,
        subnetCurrencySymbol,
        chainId,
        subnetRegistrator,
        admin
      )
      const subnet = await subnetRegistrator.subnets(subnetId)
      expect(subnet.name).to.equal(subnetName)
      expect(subnet.currencySymbol).to.equal(subnetCurrencySymbol)
      expect(subnet.httpEndpoint).to.equal(httpEndpoint)
      expect(subnet.wsEndpoint).to.equal(wsEndpoint)
      expect(subnet.logoURL).to.equal(logoURL)
      expect(subnet.chainId).to.equal(chainId)
    })

    it('gets the subnet count', async () => {
      const { admin, subnetRegistrator } =
        await deploySubnetRegistratorFixture()
      await registerSubnet(
        httpEndpoint,
        wsEndpoint,
        logoURL,
        subnetName,
        subnetId,
        subnetCurrencySymbol,
        chainId,
        subnetRegistrator,
        admin
      )
      const count = await subnetRegistrator.getSubnetCount()
      expect(count).to.equal(1)
    })

    it('gets the subnet at a given index', async () => {
      const { admin, subnetRegistrator } =
        await deploySubnetRegistratorFixture()
      await registerSubnet(
        httpEndpoint,
        wsEndpoint,
        logoURL,
        subnetName,
        subnetId,
        subnetCurrencySymbol,
        chainId,
        subnetRegistrator,
        admin
      )
      const id = await subnetRegistrator.getSubnetIdAtIndex(0)
      expect(id).to.equal(subnetId)
    })

    it('checks if a subnet exists', async () => {
      const { admin, subnetRegistrator } =
        await deploySubnetRegistratorFixture()
      await registerSubnet(
        httpEndpoint,
        wsEndpoint,
        logoURL,
        subnetName,
        subnetId,
        subnetCurrencySymbol,
        chainId,
        subnetRegistrator,
        admin
      )
      const exists = await subnetRegistrator.subnetExists(subnetId)
      expect(exists).to.be.true
    })

    it('emits a new subnet registered event', async () => {
      const { admin, subnetRegistrator } =
        await deploySubnetRegistratorFixture()
      await expect(
        registerSubnet(
          httpEndpoint,
          wsEndpoint,
          logoURL,
          subnetName,
          subnetId,
          subnetCurrencySymbol,
          chainId,
          subnetRegistrator,
          admin
        )
      )
        .to.emit(subnetRegistrator, 'NewSubnetRegistered')
        .withArgs(subnetId)
    })
  })

  describe('removeSubnet', () => {
    it('reverts if non-admin tries to remove a subnet', async () => {
      const [, nonAdmin] = await ethers.getSigners()
      await expect(
        subnetRegistrator.connect(nonAdmin).removeSubnet(subnetId)
      ).to.be.revertedWith('Ownable: caller is not the owner')
    })

    it('reverts when removing a non-existent subnet', async () => {
      const { admin, subnetRegistrator } =
        await deploySubnetRegistratorFixture()
      await expect(
        removeSubnet(subnetId, subnetRegistrator, admin)
      ).to.be.revertedWith('Bytes32Set: key does not exist in the set.')
    })

    it('emit a subnet removed event', async () => {
      const { admin, subnetRegistrator } =
        await deploySubnetRegistratorFixture()
      await registerSubnet(
        httpEndpoint,
        wsEndpoint,
        logoURL,
        subnetName,
        subnetId,
        subnetCurrencySymbol,
        chainId,
        subnetRegistrator,
        admin
      )
      await expect(removeSubnet(subnetId, subnetRegistrator, admin))
        .to.emit(subnetRegistrator, 'SubnetRemoved')
        .withArgs(subnetId)
    })
  })

  async function registerSubnet(
    httpEndpoint: string,
    wsEndpoint: string,
    logoURL: string,
    subnetName: string,
    subnetId: string,
    subnetCurrencySymbol: string,
    chainId: number,
    subnetRegistrator: Contract,
    admin: Wallet
  ) {
    return await subnetRegistrator
      .connect(admin)
      .registerSubnet(
        httpEndpoint,
        wsEndpoint,
        logoURL,
        subnetName,
        subnetId,
        subnetCurrencySymbol,
        chainId
      )
  }

  async function removeSubnet(
    subnetId: string,
    subnetRegistrator: Contract,
    admin: Wallet
  ) {
    return await subnetRegistrator.connect(admin).removeSubnet(subnetId)
  }
})
