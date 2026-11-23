"""On-chain receipt helpers for the Binance Agent ID Hackathon.

Builds the unsigned transaction for ``CMCQueryReceipt.recordQuery`` —
the user signs and submits it in their own wallet (Binance Wallet /
MetaMask, Remix, or BscScan Write). This module never holds a private
key, never signs, and never broadcasts a transaction.

Two modes:
- Offline (default): hash the query, ABI-encode ``recordQuery`` call
  data, print the unsigned tx template. Works before the contract is
  deployed — pass ``--contract`` once it has an address.
- ``--check <address>``: read-only ``eth_call`` to ``holdsAgentId``
  on the deployed contract, so the user can confirm the Agent ID gate
  passes before spending gas. Needs ``--contract`` and an RPC URL.
"""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request

from .keccak import keccak256

AGENT_ID_CONTRACT = "0x60B9262456dE011F7d15a54CdD8c48bAaa8B022F"
DEFAULT_RPC = "https://bsc-dataseed.binance.org/"

_ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")


class RecordError(ValueError):
    """Raised for bad record input or a failed read-only RPC check."""


def validate_symbol(symbol: str) -> str:
    """Normalise a symbol the way the contract requires (1-16 chars)."""
    sym = (symbol or "").strip().upper()
    if not sym:
        raise RecordError("symbol must not be empty")
    if len(sym) > 16:
        raise RecordError(f"symbol {sym!r} is {len(sym)} chars; contract allows at most 16")
    return sym


def validate_address(address: str, what: str = "address") -> str:
    addr = (address or "").strip()
    if not _ADDRESS_RE.match(addr):
        raise RecordError(f"{what} {addr!r} is not a 0x-prefixed 40-hex-char address")
    return addr


def query_hash(query: str) -> bytes:
    """keccak256 of the query text (question + answer evidence)."""
    return keccak256(query.encode("utf-8"))


def function_selector(signature: str) -> bytes:
    return keccak256(signature.encode("ascii"))[:4]


def _abi_encode_string(value: str) -> bytes:
    raw = value.encode("utf-8")
    padded_len = ((len(raw) + 31) // 32) * 32
    return (
        len(raw).to_bytes(32, "big")
        + raw
        + b"\x00" * (padded_len - len(raw))
    )


def encode_record_calldata(qhash: bytes, symbol: str) -> bytes:
    """ABI-encode recordQuery(bytes32 queryHash, string symbol)."""
    if len(qhash) != 32:
        raise RecordError("queryHash must be 32 bytes")
    sym = validate_symbol(symbol)
    # head: bytes32 value, then offset 64 for the dynamic string.
    return (
        function_selector("recordQuery(bytes32,string)")
        + qhash
        + (64).to_bytes(32, "big")
        + _abi_encode_string(sym)
    )


def encode_holds_agent_id_calldata(address: str) -> bytes:
    """ABI-encode holdsAgentId(address) for an eth_call."""
    addr = validate_address(address, "holder address")
    return function_selector("holdsAgentId(address)") + bytes.fromhex(addr[2:]).rjust(32, b"\x00")


def check_holds_agent_id(rpc_url: str, contract: str, address: str,
                         timeout: int = 15) -> bool:
    """Read-only check: does *address* hold an Agent ID? (eth_call)."""
    contract = validate_address(contract, "contract address")
    payload = json.dumps({
        "jsonrpc": "2.0", "id": 1, "method": "eth_call",
        "params": [{
            "to": contract,
            "data": "0x" + encode_holds_agent_id_calldata(address).hex(),
        }, "latest"],
    }).encode("utf-8")
    req = urllib.request.Request(
        rpc_url, data=payload,
        headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise RecordError(f"RPC call failed ({rpc_url}): {exc}") from exc
    if "error" in body:
        raise RecordError(f"RPC error: {body['error']}")
    result = body.get("result")
    if not isinstance(result, str) or not result.startswith("0x"):
        raise RecordError(f"unexpected RPC result: {body!r}")
    return int(result, 16) != 0
