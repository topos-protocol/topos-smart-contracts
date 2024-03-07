import { task } from 'hardhat/config'

enum SupportedTypechainTargets {
  'ethers-v5' = 'ethers-v5',
  'ethers-v6' = 'ethers-v6',
  'truffle-v4' = 'truffle-v4',
  'truffle-v5' = 'truffle-v5',
  'web3-v1' = 'web3-v1',
}

/**
 * This task overrides the original compile task to allow for setting the Typechain target
 * via several methods:
 * 1. Command line argument: `npx hardhat compile --typechain ethers-v5`
 * 2. Environment variable: `TYPECHAIN_TARGET=ethers-v5 npx hardhat compile`
 * 3. Hardhat config: `const config: HardhatUserConfig = { typechain: { target: 'ethers-v5' } }`
 * @param args.typechainTarget (optional) The Typechain target to build for
 */
task(
  'compile',
  'Compiles the entire project, building all artifacts and custom Typechain typings'
)
  .addOptionalParam('typechainTarget', 'The Typechain target to build for')
  .setAction(async (args, hre, runSuper) => {
    const typechainTarget =
      args.typechainTarget ||
      process.env.TYPECHAIN_TARGET ||
      hre.config.typechain.target // default 'ethers-v6'

    // Validate the Typechain target
    if (!Object.values(SupportedTypechainTargets).includes(typechainTarget)) {
      throw new Error(`Unsupported typechain target: ${typechainTarget}`)
    }
    // Override the Typechain target
    hre.config.typechain.target = typechainTarget
    hre.config.typechain.outDir = `typechain-types/${typechainTarget}`

    // Call the original compile task
    if (runSuper.isDefined) {
      await runSuper(args)
    }
  })
