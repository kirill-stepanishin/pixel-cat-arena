// Mints one NFT representing a legendary item instance to the given owner wallet.
// Usage: node mint-item-nft.mjs <treasury-keypair-path> <owner-wallet> <name> <symbol> <metadata-uri>
// Prints a single JSON line on stdout: {"mintAddress": "...", "signature": "..."}
import { createUmi } from "@metaplex-foundation/umi-bundle-defaults";
import { keypairIdentity, generateSigner, percentAmount, publicKey } from "@metaplex-foundation/umi";
import { createNft, mplTokenMetadata } from "@metaplex-foundation/mpl-token-metadata";
import { Keypair as Web3Keypair } from "@solana/web3.js";
import fs from "fs";

const [keypairPath, ownerWallet, name, symbol, uri] = process.argv.slice(2);
if (!keypairPath || !ownerWallet || !name || !symbol || !uri) {
  console.error(
    "Usage: node mint-item-nft.mjs <treasury-keypair-path> <owner-wallet> <name> <symbol> <metadata-uri>"
  );
  process.exit(1);
}

try {
  const secret = JSON.parse(fs.readFileSync(keypairPath, "utf8"));
  const web3Keypair = Web3Keypair.fromSecretKey(Uint8Array.from(secret));

  const umi = createUmi("https://api.devnet.solana.com").use(mplTokenMetadata());
  const treasury = umi.eddsa.createKeypairFromSecretKey(web3Keypair.secretKey);
  umi.use(keypairIdentity(treasury));

  const mint = generateSigner(umi);
  const { signature } = await createNft(umi, {
    mint,
    name,
    symbol,
    uri,
    sellerFeeBasisPoints: percentAmount(0),
    tokenOwner: publicKey(ownerWallet),
  }).sendAndConfirm(umi);

  process.stdout.write(
    JSON.stringify({
      mintAddress: mint.publicKey,
      signature: Buffer.from(signature).toString("hex"),
    }) + "\n"
  );
} catch (err) {
  console.error(err.message ?? String(err));
  process.exit(1);
}
