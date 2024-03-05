import { HardhatUserConfig } from 'hardhat/config'
import '@nomicfoundation/hardhat-toolbox'

import './tasks/compile'

const config: HardhatUserConfig = {
  solidity: {
    version: '0.8.9',
    settings: {
      optimizer: {
        enabled: true,
        runs: 1000,
      },
    },
  },
  typechain: {
    // default 'ethers-v6'
    outDir: 'typechain-types/ethers-v6',
    target: 'ethers-v6',
  },
}

export default config
