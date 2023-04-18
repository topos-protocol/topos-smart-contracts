export const INDEX_OF_TX_DATA_33 = 33
export const OUT_OF_BOUNDS_INDEX_OF_DATA_295 = 295

class TranctionData {
  proofBlob: string
  txRaw: string
  txRoot: string
  optionalData?: string[]

  constructor(
    proofBlob: string,
    txRaw: string,
    txRoot: string,
    optionalData?: string[]
  ) {
    this.proofBlob = proofBlob
    this.txRaw = txRaw
    this.txRoot = txRoot
    this.optionalData = optionalData
  }
}

export const MINT_EXCEED_TRANSACTION: TranctionData = new TranctionData(
  '0xf901380180f90133f90130822080b9012af90127078083b71b00946951b5bd8150' +
    '43e3f842c1b026b0fa888cc2dd8580b8c4b32c8105000000000000000000000000000' +
    '000000000000000000000000000000000000200000000000000000000000000630466' +
    '86e46dc6f15918b61ae2b121458534a50000000000000000000000000000000000000' +
    '000000000000000000000000080000000000000000000000000000000000000000000' +
    '000000000000000000006e00000000000000000000000000000000000000000000000' +
    '00000000000000003544b580000000000000000000000000000000000000000000000' +
    '000000000000820a95a0ba679cf4846e4dcefc3fe4e0795f4083b5330f6871baa7820' +
    '59cf9e518b6346ca05319e29ed788d7f9150d3c7e670b2fc4aca191e90dbb94594158' +
    '6927559919ed',
  '0xf90127078083b71b00946951b5bd815043e3f842c1b026b0fa888cc2dd8580b8c4' +
    'b32c81050000000000000000000000000000000000000000000000000000000000000' +
    '0020000000000000000000000000063046686e46dc6f15918b61ae2b121458534a500' +
    '000000000000000000000000000000000000000000000000000000000000800000000' +
    '00000000000000000000000000000000000000000000000000000006e000000000000' +
    '0000000000000000000000000000000000000000000000000003544b5800000000000' +
    '00000000000000000000000000000000000000000000000820a95a0ba679cf4846e4d' +
    'cefc3fe4e0795f4083b5330f6871baa782059cf9e518b6346ca05319e29ed788d7f91' +
    '50d3c7e670b2fc4aca191e90dbb945941586927559919ed',
  '0x7c09ef04b23b7a0658603b1fcc4c9c1a2a19db8e8c256311e5a34adb811e337e'
)

export const NORMAL_TRANSACTION: TranctionData = new TranctionData(
  '0xf901380180f90133f90130822080b9012af90127078083b71b00946951b5bd8150' +
    '43e3f842c1b026b0fa888cc2dd8580b8c4b32c8105000000000000000000000000' +
    '000000000000000000000000000000000000000200000000000000000000000000' +
    '63046686e46dc6f15918b61ae2b121458534a50000000000000000000000000000' +
    '000000000000000000000000000000000080000000000000000000000000000000' +
    '000000000000000000000000000000003200000000000000000000000000000000' +
    '00000000000000000000000000000003544b580000000000000000000000000000' +
    '000000000000000000000000000000820a95a005d4c8184f5a7ba13078a784a1a3' +
    'e546045b4edbfa19af57645dc65d67137f47a0186ce1a403bdbef06c71408fa9fd' +
    '7f156154eb5521a9bfda66396ab576fed518',
  '0xf90127078083b71b00946951b5bd815043e3f842c1b026b0fa888cc2dd8580b8c4' +
    'b32c81050000000000000000000000000000000000000000000000000000000000000' +
    '0020000000000000000000000000063046686e46dc6f15918b61ae2b121458534a500' +
    '000000000000000000000000000000000000000000000000000000000000800000000' +
    '000000000000000000000000000000000000000000000000000000032000000000000' +
    '0000000000000000000000000000000000000000000000000003544b5800000000000' +
    '00000000000000000000000000000000000000000000000820a95a005d4c8184f5a7b' +
    'a13078a784a1a3e546045b4edbfa19af57645dc65d67137f47a0186ce1a403bdbef06' +
    'c71408fa9fd7f156154eb5521a9bfda66396ab576fed518',
  '0x18c9ea746f244d86383dd460a7b3e78d63ae0019ab4a23250a1c1c8f081cc0a5',
  [
    '0xf901380180f90133f90130822080b9012af90127078083b71b00946951b5bd8150' +
      '43e3f842c1b026b0fa888cc2dd8580b8c4b32c8105000000000000000000000000' +
      '000000000000000000000000000000000000000200000000000000000000000000' +
      '63046686e46dc6f15918b61ae2b121458534a50000000000000000000000000000' +
      '000000000000000000000000000000000080000000000000000000000000000000' +
      '000000000000000000000000000000003200000000000000000000000000000000' +
      '00000000000000000000000000000003544b580000000000000000000000000000' +
      '000000000000000000000000000000820a95a005d4c8184f5a7ba13078a784a1a3' +
      'e546045b4edbfa19af57645dc65d67137f47a0186ce1a403bdbef06c71408fa9fd' +
      '7f156154eb5521a9bfda66396ab576fe0d12',
  ]
)

export const ZERO_ADDRESS_TRANSACTION: TranctionData = new TranctionData(
  '0xf901380180f90133f90130822080b9012af90127078083b71b00946951b5bd8150' +
    '43e3f842c1b026b0fa888cc2dd8580b8c4b32c8105000000000000000000000000000' +
    '000000000000000000000000000000000000200000000000000000000000000000000' +
    '000000000000000000000000000000000000000000000000000000000000000000000' +
    '000000000000000000000000080000000000000000000000000000000000000000000' +
    '000000000000000000003200000000000000000000000000000000000000000000000' +
    '00000000000000003544b580000000000000000000000000000000000000000000000' +
    '000000000000820a96a09bf245e0c34b2e20cb7f40da07791ad8a6424006bb2f4a790' +
    'fc0a54a1cca6929a051a620aa1a4e60cc414982e09809ee24c8c24a53ace81a5eae22' +
    'f5e36136945e',
  '0xf90127078083b71b00946951b5bd815043e3f842c1b026b0fa888cc2dd8580b8c4' +
    'b32c81050000000000000000000000000000000000000000000000000000000000000' +
    '002000000000000000000000000000000000000000000000000000000000000000000' +
    '000000000000000000000000000000000000000000000000000000000000800000000' +
    '000000000000000000000000000000000000000000000000000000032000000000000' +
    '0000000000000000000000000000000000000000000000000003544b5800000000000' +
    '00000000000000000000000000000000000000000000000820a96a09bf245e0c34b2e' +
    '20cb7f40da07791ad8a6424006bb2f4a790fc0a54a1cca6929a051a620aa1a4e60cc4' +
    '14982e09809ee24c8c24a53ace81a5eae22f5e36136945e',
  '0x326138f08ae41877544bbac9932b51ea75fa043ea6d571aa0dae550eda5c0858'
)