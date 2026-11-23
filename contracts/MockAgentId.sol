// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title MockAgentId
/// @notice TESTNET ONLY mock of the SPACE ID Agent ID registry.
/// @dev Mirrors the one function CMCQueryReceipt uses: balanceOf.
/// Mint yourself a mock ID to test the gate on BSC testnet.
/// Never deploy this on mainnet; mainnet uses the real registry at
/// 0x60B9262456dE011F7d15a54CdD8c48bAaa8B022F.
contract MockAgentId {
    mapping(address => uint256) public balanceOf;

    event MockIdMinted(address indexed to);

    /// @notice Mint one mock Agent ID to `to`. Anyone can call this on testnet.
    function mint(address to) external {
        require(balanceOf[to] == 0, "MockAgentId: already has one");
        balanceOf[to] = 1;
        emit MockIdMinted(to);
    }
}
