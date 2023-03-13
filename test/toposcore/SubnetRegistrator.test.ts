import { Contract } from 'ethers';
import { ethers } from 'hardhat';
import { expect } from 'chai';

describe('SubnetRegistrator', () => {
  let subnetRegistrator: Contract;

  const endpoint = 'http://127.0.0.1';
  const logoURL = 'http://image-url.com';
  const subnetName = 'Test Subnet';
  const subnetId =
    '0x0000000000000000000000000000000000000000000000000000000000000001';
  const subnetCurrencySymbol = 'SUB';
  const chainId = 1;

  beforeEach(async () => {
    const SubnetRegistrator = await ethers.getContractFactory(
      'SubnetRegistrator',
    );
    subnetRegistrator = await SubnetRegistrator.deploy();

    await subnetRegistrator.registerSubnet(
      endpoint,
      logoURL,
      subnetName,
      subnetId,
      subnetCurrencySymbol,
      chainId,
    );
  });

  it('registers a subnet', async () => {
    const subnet = await subnetRegistrator.subnets(subnetId);
    expect(subnet.name).to.equal(subnetName);
    expect(subnet.currencySymbol).to.equal(subnetCurrencySymbol);
    expect(subnet.endpoint).to.equal(endpoint);
    expect(subnet.logoURL).to.equal(logoURL);
    expect(subnet.chainId).to.equal(chainId);
  });

  it('reverts when removing a non-existent subnet', async () => {
    await subnetRegistrator.removeSubnet(subnetId);
    await expect(subnetRegistrator.removeSubnet(subnetId)).to.be.revertedWith(
      'Bytes32Set: key does not exist in the set.',
    );
  });

  it('removes a subnet', async () => {
    const tx = await subnetRegistrator.removeSubnet(subnetId);
    await expect(tx)
      .to.emit(subnetRegistrator, 'SubnetRemoved')
      .withArgs(subnetId);
  });

  it('returns the number of subnets', async () => {
    const count = await subnetRegistrator.getSubnetCount();
    expect(count).to.equal(1);
  });

  it('returns the subnet at a given index', async () => {
    const id = await subnetRegistrator.getSubnetIdAtIndex(0);
    expect(id).to.equal(subnetId);
  });

  it('checks if a subnet exists', async () => {
    const exists = await subnetRegistrator.subnetExists(subnetId);
    expect(exists).to.be.true;
  });
});
