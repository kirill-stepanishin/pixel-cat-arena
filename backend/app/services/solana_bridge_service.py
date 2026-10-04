"""Thin async wrapper around the Node.js scripts in solana_bridge/.

The Metaplex/Solana SDKs used for minting are JS-only, so the prototype shells
out to small Node scripts rather than reimplementing NFT minting in Python.
Each script prints a single JSON line on stdout; warnings/errors go to stderr.
"""
from __future__ import annotations

import asyncio
import json
from pathlib import Path

import base58
from nacl.exceptions import BadSignatureError
from nacl.signing import VerifyKey

from app.config import get_settings


def claim_message(mint_address: str) -> str:
    """Deterministic message a wallet signs (off-chain, free, no gas) to prove ownership."""
    return f"pixel-cat-arena:claim:{mint_address}"


def verify_wallet_signature(wallet_address: str, message: str, signature_base58: str) -> bool:
    """Verify an ed25519 signature produced by a Solana wallet's signMessage. No funds
    or transactions are involved — this only proves control of the private key."""
    try:
        verify_key = VerifyKey(base58.b58decode(wallet_address))
        verify_key.verify(message.encode("utf-8"), base58.b58decode(signature_base58))
        return True
    except (BadSignatureError, ValueError, TypeError):
        return False


class SolanaBridgeError(Exception):
    pass


def _bridge_dir() -> Path:
    settings = get_settings()
    path = Path(settings.solana_bridge_dir)
    if not path.is_absolute():
        # Resolve relative to the backend/ directory regardless of CWD.
        path = Path(__file__).resolve().parents[2] / settings.solana_bridge_dir
    return path


async def _run_script(script_name: str, *args: str) -> dict:
    settings = get_settings()
    script_path = _bridge_dir() / script_name
    process = await asyncio.create_subprocess_exec(
        settings.solana_node_binary,
        str(script_path),
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=str(_bridge_dir()),
    )
    stdout, stderr = await process.communicate()
    if process.returncode != 0:
        raise SolanaBridgeError(stderr.decode().strip() or f"{script_name} failed")
    try:
        return json.loads(stdout.decode().strip().splitlines()[-1])
    except (json.JSONDecodeError, IndexError) as exc:
        raise SolanaBridgeError(f"{script_name} returned unparseable output") from exc


async def mint_nft(owner_wallet: str, name: str, symbol: str, metadata_uri: str) -> dict:
    settings = get_settings()
    keypair_path = Path(settings.solana_treasury_keypair_path)
    if not keypair_path.is_absolute():
        keypair_path = Path(__file__).resolve().parents[2] / settings.solana_treasury_keypair_path
    return await _run_script(
        "mint-item-nft.mjs", str(keypair_path), owner_wallet, name, symbol, metadata_uri
    )


async def check_holder(mint_address: str, candidate_wallet: str) -> bool:
    result = await _run_script("check-holder.mjs", mint_address, candidate_wallet)
    return bool(result.get("holds", False))
