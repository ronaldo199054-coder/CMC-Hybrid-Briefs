# contracts/

## CMCQueryReceipt.sol

Minimal receipt registry for the CMC Research Agent — the on-chain piece for
the Binance Wallet × BNB Chain Agent ID Hackathon (Agent ID Ecosystem Pioneer
Award, submission closes 2026-12-09 08:00 UTC / 16:00 Beijing).

### How it works

- Agent ID holders call `recordQuery(queryHash, symbol)` to store a receipt
  proving they ran a CMC query. `queryHash` is the keccak256 hash of the
  query (question + answer evidence); `symbol` is a short token symbol
  (e.g. `"BTC"`, max 16 chars).
- The contract checks the caller holds an Agent ID by calling `balanceOf`
  on the SPACE ID Agent ID contract (ERC-721, BNB Chain):
  `0x60b9262456de011f7d15a54cdd8c48baaa8b022f`. `balanceOf > 0` means holder.
- `holdsAgentId(address)` is a public view helper for the CLI and off-chain
  checks.
- Every record emits `QueryRecorded(id, agent, queryHash, symbol, timestamp)`.
  The Pioneer Award ranking counts interactions with this contract by Agent
  ID addresses (address count, volume, tx count).

### Safety / hackathon red lines

- No owner, no admin functions, no upgradeability, holds no funds. There are
  no owner permissions to disclose.
- The contract never asks for keys or signatures beyond the user's own
  transaction: the user signs `recordQuery` themselves in their own wallet.
- No QR-code login, no session storage, no auto-transfers, no promised
  returns.

### Deploy

The Agent ID registry address is a constructor argument, so the same code
runs on testnet (against a mock) and mainnet (against the real registry).

#### BSC testnet first (free)

1. Get test BNB from the BNB Chain testnet faucet.
2. Open Remix, create `CMCQueryReceipt.sol` and `MockAgentId.sol`, paste the
   files, compiler 0.8.20 or newer matching the pragma.
3. Connect your wallet (MetaMask / Binance Wallet) on BSC Testnet
   (chain 97) and deploy `MockAgentId`, then call `mint(your address)` to
   give yourself a mock Agent ID.
4. Deploy `CMCQueryReceipt` with the mock's address as the constructor
   argument, then call `recordQuery` from your address to test the gate.
   Anyone without a mock ID gets rejected.
5. Verify on testnet BscScan if you want the practice run.

Why a mock: the real Agent ID registry only exists on mainnet, so the
mainnet address cannot be tested on testnet. The mock mirrors exactly the
one function used (`balanceOf`).

#### BNB Smart Chain mainnet (counts for the submission)

1. Switch your wallet to BSC mainnet (chain 56). Keep a little BNB for gas
   (a small contract like this is usually well under a dollar).
2. In Remix, deploy `CMCQueryReceipt` with constructor argument
   `0x60B9262456dE011F7d15a54CdD8c48bAaa8B022F` (the real SPACE ID Agent ID
   registry).
3. Verify on BscScan: Contract → Verify & Publish, single file, MIT,
   compiler version matching your compile, optimization off (or match your
   settings). BscScan needs the constructor argument — Remix's verification
   plugin fills it in automatically, or paste the ABI-encoded address.
4. Record the deployed address — it goes into the hackathon submission
   (project name, website, contract address, Agent ID usage description)
   and into the landing page.

Only the mainnet address counts for the submission.

### Next steps

- CLI `record` command: done (`python -m cmc_agent record BTC --query "brief BTC"`).
  It hashes the query (keccak256, pure-Python, no new dependency), ABI-encodes
  `recordQuery` call data, and prints an unsigned tx template — the user signs
  in their own wallet, the agent never holds keys or broadcasts. `--check`
  does a read-only `holdsAgentId` call first so a non-holder does not waste
  gas. Until the contract is deployed it prints the hash + call data with no
  address to send to; re-run with `--contract <deployed address>` after deploy.
- Testnet deploy first (free test BNB), then mainnet deploy + BscScan verify.
- Submission before 2026-12-09 16:00 Beijing; then drive Agent ID holders to
  interact — the Pioneer ranking is on-chain activity, not judged code.
