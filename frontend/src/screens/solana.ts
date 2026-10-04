import { claimItemNft, getClaimableItems, mintItemNft } from "../api/gameApi";
import { claimMessage, isPhantomInstalled, signWithPhantom } from "../solana/phantom";
import type { ItemInstanceRead } from "../types";
import { escapeHtml, itemTip, slotIcon, statChips, tipAttr, toast } from "./ui";

const EXPLORER_BASE = "https://explorer.solana.com/address";

export function solanaExplorerUrl(mintAddress: string): string {
  return `${EXPLORER_BASE}/${mintAddress}?cluster=devnet`;
}

let claimable: ItemInstanceRead[] = [];
let lastWallet = "";
let busyMintAddress: string | null = null;

export function solanaMarkup(): string {
  return `
    <section class="panel solana-panel" id="solana-panel">
      <div class="panel-header compact">
        <div>
          <p class="eyebrow">⛓ SOLANA (DEVNET)</p>
          <h3>Claim on-chain items</h3>
        </div>
      </div>
      <p class="market-hint">
        Legendary gear exported to Solana can be traded wallet-to-wallet outside the game.
        Paste a devnet wallet address to see what it currently holds, then claim an item back
        into your account — claiming proves you control the wallet with a free signature, no
        transaction or fees.
      </p>
      <div class="solana-lookup">
        <input type="text" id="solana-wallet" placeholder="Devnet wallet address" aria-label="Wallet address to check" />
        <button type="button" class="ghost-button" id="solana-check">Check wallet</button>
      </div>
      <div class="market-listings" id="solana-claimable"></div>
    </section>`;
}

function claimableCard(item: ItemInstanceRead): string {
  const rarity = item.definition.rarity;
  const busy = busyMintAddress === item.solana_mint_address;
  const mint = item.solana_mint_address ?? "";
  return `
    <article class="listing-card rarity-card-${rarity}" ${tipAttr(itemTip(item))}>
      <div class="inventory-card-top">
        <span class="slot-icon">${slotIcon(item.definition.slot)}</span>
        <div>
          <strong class="rarity-${rarity}">${escapeHtml(item.definition.name)}</strong>
          <span>${item.definition.slot} · ${rarity}</span>
        </div>
      </div>
      <div class="stat-chips">${statChips(item)}</div>
      <p class="listing-seller">
        <a href="${solanaExplorerUrl(mint)}" target="_blank" rel="noopener">View mint on Explorer ↗</a>
      </p>
      <div class="listing-foot">
        <span></span>
        <button type="button" class="primary-button" data-claim-mint="${mint}" ${busy ? "disabled" : ""}>
          ${busy ? "Claiming…" : "Claim"}
        </button>
      </div>
    </article>`;
}

function renderClaimable(root: HTMLElement): void {
  const container = root.querySelector<HTMLElement>("#solana-claimable");
  if (!container) return;
  if (!lastWallet) {
    container.innerHTML = '<p class="empty-message">Paste a wallet address and check it to see claimable items.</p>';
    return;
  }
  container.innerHTML = claimable.length
    ? claimable.map(claimableCard).join("")
    : '<p class="empty-message">That wallet isn\'t holding any items this account doesn\'t already own.</p>';
}

export function mountSolana(root: HTMLElement, onInventoryChange: () => Promise<void>): void {
  root.querySelector("#solana-check")?.addEventListener("click", async () => {
    const input = root.querySelector<HTMLInputElement>("#solana-wallet");
    const wallet = input?.value.trim();
    if (!wallet) {
      toast("Enter a wallet address first.", "error");
      return;
    }
    lastWallet = wallet;
    const container = root.querySelector<HTMLElement>("#solana-claimable");
    if (container) container.innerHTML = '<p class="empty-message">Checking wallet…</p>';
    try {
      claimable = await getClaimableItems(wallet);
    } catch (error) {
      toast(error instanceof Error ? error.message : "Could not check wallet.", "error");
      claimable = [];
    }
    renderClaimable(root);
  });

  root.addEventListener("click", async (event) => {
    const target = event.target as HTMLElement;

    const exportButton = target.closest<HTMLButtonElement>("[data-export-confirm]");
    if (exportButton?.dataset.itemId) {
      const card = exportButton.closest(".card-sub");
      const walletInput = card?.querySelector<HTMLInputElement>("[data-export-wallet]");
      const wallet = walletInput?.value.trim();
      if (!wallet) {
        toast("Enter a devnet wallet address to receive the NFT.", "error");
        return;
      }
      exportButton.disabled = true;
      exportButton.textContent = "Minting…";
      try {
        await mintItemNft(exportButton.dataset.itemId, wallet);
        toast("Minted! The item is now on Solana — check Explorer from its card.", "ok");
      } catch (error) {
        toast(error instanceof Error ? error.message : "Could not mint this item.", "error");
      }
      await onInventoryChange();
      return;
    }

    const claimButton = target.closest<HTMLButtonElement>("[data-claim-mint]");
    if (!claimButton?.dataset.claimMint) return;

    const mintAddress = claimButton.dataset.claimMint;
    busyMintAddress = mintAddress;
    renderClaimable(root);
    try {
      if (!isPhantomInstalled()) {
        throw new Error("Install Phantom (phantom.app) to sign the free ownership proof.");
      }
      const { walletAddress, signature } = await signWithPhantom(claimMessage(mintAddress));
      const claimed = await claimItemNft(mintAddress, walletAddress, signature);
      toast(`Claimed ${claimed.definition.name}! It's back in your backpack.`, "ok");
      claimable = claimable.filter((item) => item.solana_mint_address !== mintAddress);
      await onInventoryChange();
    } catch (error) {
      toast(error instanceof Error ? error.message : "Could not claim item.", "error");
    }
    busyMintAddress = null;
    renderClaimable(root);
  });
}
