// SPDX-License-Identifier: MIT
pragma solidity ^0.8.2;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "../../contracts/topos-core-contracts/CrossSubnetInterface.sol";

interface IToposERC20Base is IERC20 {
    function sendToSubnet(CrossSubnetInterface.CrossSubnetMessage memory xsMsg) external;

    function mintFromXsMsg(bytes calldata certId, bytes calldata xsMsgId) external;

    function transferXsMsgFee(
        bytes calldata certId,
        bytes calldata xsMsgId,
        address receiver
    ) external;

    function addProcessedXsMessage(bytes32 xSMsgHash) external;
}
