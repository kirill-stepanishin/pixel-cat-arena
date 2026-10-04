// Checks whether a candidate wallet currently holds a given NFT mint (supply of 1).
// Usage: node check-holder.mjs <mint-address> <candidate-wallet>
// Prints a single JSON line on stdout: {"holds": true|false}
import { Connection, clusterApiUrl, PublicKey } from "@solana/web3.js";
import { getAssociatedTokenAddress } from "@solana/spl-token";

const [mintAddress, candidateWallet] = process.argv.slice(2);
if (!mintAddress || !candidateWallet) {
  console.error("Usage: node check-holder.mjs <mint-address> <candidate-wallet>");
  process.exit(1);
}

try {
  const connection = new Connection(clusterApiUrl("devnet"), "confirmed");
  const mint = new PublicKey(mintAddress);
  const candidate = new PublicKey(candidateWallet);
  const ata = await getAssociatedTokenAddress(mint, candidate);

  let holds = false;
  try {
    const balance = await connection.getTokenAccountBalance(ata);
    holds = balance.value.uiAmount === 1;
  } catch {
    holds = false;
  }
  process.stdout.write(JSON.stringify({ holds }) + "\n");
} catch (err) {
  console.error(err.message ?? String(err));
  process.exit(1);
}
