// SPDX-License-Identifier: MIT
pragma solidity ^0.8.9;

type PeerId is bytes32;

contract TCENodeRegistrator {
    struct TCENode {
        PeerId peerId;
        bool isPresent;
    }

    /// @notice Mapping to store the registered TCE nodes
    /// @dev PeerId => TCENode
    mapping(PeerId => TCENode) public tceNodes;

    /// @notice New TCE node registration event
    event NewTCENodeRegistered(PeerId peerId);

    /// @notice TCE node removal event
    event TCENodeRemoved(PeerId peerId);

    error TCENodeAlreadyRegistered(PeerId peerId);
    error TCENodeNotRegistered(PeerId peerId);

    /// @notice Register a new TCE node
    /// @param peerId peer ID of the TCE node
    function registerTCENode(PeerId peerId) public {
        if (tceNodes[peerId].isPresent) revert TCENodeAlreadyRegistered(peerId);
        TCENode memory tceNode = TCENode(peerId, true);
        tceNodes[peerId] = tceNode;
        emit NewTCENodeRegistered(peerId);
    }

    /// @notice Remove an already registered TCE node
    /// @param peerId peer ID of the TCE node
    function removeTCENode(PeerId peerId) public {
        if (!tceNodes[peerId].isPresent) revert TCENodeNotRegistered(peerId);
        delete tceNodes[peerId];
        emit TCENodeRemoved(peerId);
    }
}
