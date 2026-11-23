// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title CMCQueryReceipt
/// @notice Minimal receipt registry for the CMC Research Agent.
/// @dev Built for the Binance Wallet x BNB Chain Agent ID Hackathon
/// (Agent ID Ecosystem Pioneer Award). Only addresses holding a Binance
/// Agent ID (name.ai) can record a receipt. Agent ID is the SPACE ID
/// ERC-721 on BNB Chain; holding is checked with balanceOf > 0.
/// The contract holds no funds, has no owner, no admin functions,
/// and is not upgradeable.
interface IAgentId {
    function balanceOf(address owner) external view returns (uint256);
}

contract CMCQueryReceipt {
    /// @notice Agent ID registry contract (SPACE ID ERC-721, non-transferable).
    /// Mainnet (BNB Chain): 0x60B9262456dE011F7d15a54CdD8c48bAaa8B022F.
    /// Passed in the constructor so the same code can be tested on testnet
    /// against a mock registry.
    IAgentId public immutable AGENT_ID;

    /// @param agentId Address of the Agent ID registry contract.
    constructor(address agentId) {
        require(agentId != address(0), "CMCQueryReceipt: zero Agent ID");
        AGENT_ID = IAgentId(agentId);
    }

    struct Receipt {
        address agent;
        bytes32 queryHash;
        string symbol;
        uint256 timestamp;
    }

    uint256 public receiptCount;
    mapping(uint256 => Receipt) public receipts;
    mapping(address => uint256) public receiptsByAgent;

    event QueryRecorded(
        uint256 indexed id,
        address indexed agent,
        bytes32 indexed queryHash,
        string symbol,
        uint256 timestamp
    );

    /// @notice Returns true if `account` holds at least one Agent ID.
    function holdsAgentId(address account) public view returns (bool) {
        return AGENT_ID.balanceOf(account) > 0;
    }

    /// @notice Record a CMC query receipt. Caller must hold an Agent ID.
    /// @param queryHash keccak256 hash of the query (question + answer evidence).
    /// @param symbol Short token symbol the query was about, e.g. "BTC".
    /// @return id The new receipt id.
    function recordQuery(bytes32 queryHash, string calldata symbol)
        external
        returns (uint256 id)
    {
        require(holdsAgentId(msg.sender), "CMCQueryReceipt: no Agent ID");
        require(bytes(symbol).length > 0, "CMCQueryReceipt: empty symbol");
        require(bytes(symbol).length <= 16, "CMCQueryReceipt: symbol too long");

        id = receiptCount;
        receipts[id] = Receipt({
            agent: msg.sender,
            queryHash: queryHash,
            symbol: symbol,
            timestamp: block.timestamp
        });
        receiptsByAgent[msg.sender] += 1;
        receiptCount += 1;

        emit QueryRecorded(id, msg.sender, queryHash, symbol, block.timestamp);
    }

    /// @notice Fetch one receipt by id.
    function getReceipt(uint256 id) external view returns (Receipt memory) {
        require(id < receiptCount, "CMCQueryReceipt: bad id");
        return receipts[id];
    }
}
