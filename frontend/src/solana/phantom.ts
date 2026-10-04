// Minimal Phantom wallet hook — no wallet-adapter dependency. Used only to prove
// control of a wallet's private key by signing a free, off-chain message (no
// transaction, no fees, no fund risk). Exporting an item to Solana never needs
// this; only claiming an on-chain item back into the game does.
import bs58 from "bs58";

interface PhantomProvider {
  isPhantom?: boolean;
  publicKey?: { toString(): string } | null;
  connect(): Promise<{ publicKey: { toString(): string } }>;
  signMessage(message: Uint8Array, display: "utf8"): Promise<{ signature: Uint8Array }>;
}

function getProvider(): PhantomProvider | null {
  const candidate = (window as unknown as { solana?: PhantomProvider }).solana;
  return candidate?.isPhantom ? candidate : null;
}

export function isPhantomInstalled(): boolean {
  return getProvider() !== null;
}

export function claimMessage(mintAddress: string): string {
  return `pixel-cat-arena:claim:${mintAddress}`;
}

/**
 * Connects to Phantom (if needed) and signs `message`, returning the connected
 * wallet address and a base58-encoded ed25519 signature ready for the claim API.
 */
export async function signWithPhantom(
  message: string,
): Promise<{ walletAddress: string; signature: string }> {
  const provider = getProvider();
  if (!provider) {
    throw new Error("Phantom wallet not found. Install it from phantom.app to claim items.");
  }
  const { publicKey } = await provider.connect();
  const encoded = new TextEncoder().encode(message);
  const { signature } = await provider.signMessage(encoded, "utf8");
  return { walletAddress: publicKey.toString(), signature: bs58.encode(signature) };
}
