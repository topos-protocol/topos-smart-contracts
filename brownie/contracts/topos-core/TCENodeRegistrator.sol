// SPDX-License-Identifier: MIT
pragma solidity ^0.8.9;

type PeerId is bytes32; // type of peer IDs

contract TCENodeRegistrator {
    error TCENodeAlreadyRegistered(PeerId peerId);

    struct TCENode {
        PeerId peerId;
        bool isPresent;
    }

    /// @notice Mapping to store the registered TCE nodes
    /// @dev PeerId => TCENode
    mapping(PeerId => TCENode) tceNodes;

    /// @notice New TCE node registration event
    event NewTCENodeRegistered(PeerId peerId);

    /// @notice Register a new TCE node
    /// @param peerId peer ID of the TCE node
    function registerTCENode(PeerId peerId) public {
        if (tceNodes[peerId].isPresent) revert TCENodeAlreadyRegistered(peerId);
        TCENode memory tceNode = TCENode(peerId, true);
        tceNodes[peerId] = tceNode;
        emit NewTCENodeRegistered(peerId);
    }
}
