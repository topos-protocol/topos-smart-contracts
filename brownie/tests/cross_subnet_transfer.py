import pytest
import brownie


def test_deployment(alice, validator, sendingContracts):
    (subnetAToken, subnetATCC) = sendingContracts
    initialMintAmount = 1e23
    assert subnetAToken.balanceOf(alice) == initialMintAmount
    assert subnetATCC.hasRole(
        "0xa95257aebefccffaada4758f028bce81ea992693be70592f620c4c9a0d9e715a",
        validator,
    )


def test_send_to_subnet_event_fires(
    alice, bob, subnetBId, dummyMsgId, sendingContracts, receivingContracts
):
    (subnetAToken, _) = sendingContracts
    (subnetBToken, _) = receivingContracts
    amount = subnetAToken.balanceOf(alice) / 4
    feeAmount = 100
    xsAssetTransfer = [subnetBToken.address, bob, alice, amount]
    emptyXsRemoteCall = [brownie.ZERO_ADDRESS, "0x00", ["0x00"]]
    xsFee = [subnetBToken.address, feeAmount]
    xsTransactionType = 0
    xsMsg = [
        dummyMsgId,
        subnetBId,
        xsAssetTransfer,
        emptyXsRemoteCall,
        xsFee,
        xsTransactionType,
    ]

    tx = subnetAToken.sendToSubnet(xsMsg)
    assert len(tx.events) == 2
    # burn event
    assert tx.events["Transfer"].values() == [
        alice,
        brownie.ZERO_ADDRESS,
        amount,
    ]
    # Asset transfer record event
    assert tx.events["AssetTransferTxSent"].values() == [
        dummyMsgId,
        xsAssetTransfer,
        xsFee,
        xsTransactionType,
    ]


def test_cross_subnet_asset_transfer(
    alice,
    bob,
    charlie,
    validator,
    subnetAId,
    subnetBId,
    dummyCertId,
    dummyPrevCertId,
    dummyMsgId,
    sendingContracts,
    receivingContracts,
):
    (subnetAToken, subnetATCC) = sendingContracts
    (subnetBToken, subnetBTCC) = receivingContracts
    amount = subnetAToken.balanceOf(alice) / 4
    feeAmount = 100
    xsAssetTransfer = [subnetBToken.address, bob, alice, amount]
    emptyXsRemoteCall = [brownie.ZERO_ADDRESS, "0x00", ["0x00"]]
    xsFee = [subnetBToken.address, feeAmount]
    xsTransactionType = 0  # 0=AssetTransfer, 1=RemoteContractCall
    xsMsg = [
        dummyMsgId,
        subnetBId,
        xsAssetTransfer,
        emptyXsRemoteCall,
        xsFee,
        xsTransactionType,
    ]

    cert = [subnetAId, dummyCertId, dummyPrevCertId, True, [xsMsg]]
    subnetBTCC.verifyCertificate(
        cert, {"from": validator}
    )  # only validator can call `verifyCertificate`
    storedCert = subnetBTCC.validatedCerts(cert[1])
    assert storedCert[3] == True

    subnetBTCC.executeXsMessage(cert[1], xsMsg[0], {"from": charlie})
    assert subnetBToken.balanceOf(bob) == amount
    # Charlie is the sender of `executeXsMessage` so he gets the fees
    assert subnetBToken.balanceOf(charlie) == feeAmount
