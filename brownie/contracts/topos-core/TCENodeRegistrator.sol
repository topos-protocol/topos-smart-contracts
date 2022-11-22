// SPDX-License-Identifier: MIT
pragma solidity ^0.8.9;

contract TCENodeRegistrator {
    error TCENodeAlreadyRegistered(bytes peerId);

    struct TCENode {
        bytes peerId;
        bool isPresent;
    }

    /// @notice Mapping to store the registered TCE nodes
    /// @dev PeerId => TCENode
    mapping(bytes => TCENode) tceNodes;

    /// @notice New TCE node registration event
    event NewTCENodeRegistered(bytes peerId);

    /// @notice Register a new TCE node
    /// @param peerId peer ID of the TCE node
    function registerTCENode(bytes calldata peerId) public {
        if (tceNodes[peerId].isPresent) revert TCENodeAlreadyRegistered(peerId);
        TCENode memory tceNode = TCENode(peerId, true);
        tceNodes[peerId] = tceNode;
        emit NewTCENodeRegistered(peerId);
    }
}
