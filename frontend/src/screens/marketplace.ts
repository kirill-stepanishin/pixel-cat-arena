import {
  cancelListing,
  createListing,
  getListings,
  purchaseListing,
  sellItem,
  type ListingScope,
} from "../api/gameApi";
import type { ListingRead } from "../types";
import { escapeHtml, itemTip, slotIcon, statChips, tipAttr, toast, uiContext } from "./ui";

const SLOTS = ["head", "body", "weapon", "accessory"];
const RARITIES = ["common", "rare", "epic", "legendary"];

let myListings = new Map<string, ListingRead>();
let scope: ListingScope = "others";
let slotFilter = "";
let rarityFilter = "";
let busyId: string | null = null;

export function getListedItem(itemId: string): ListingRead | undefined {
  return myListings.get(itemId);
}

export function marketplaceMarkup(): string {
  const options = (values: string[], label: string): string =>
    `<option value="">${label}</option>${values.map((value) => `<option value="${value}">${value}</option>`).join("")}`;
  return `
    <section class="panel market-panel" id="market-panel">
      <div class="panel-header compact">
        <div>
          <p class="eyebrow">MARKETPLACE</p>
          <h3>Trade with other cats</h3>
        </div>
        <div class="mode-tabs" role="tablist">
          <button type="button" class="mode-tab active" data-market-scope="others">Browse</button>
          <button type="button" class="mode-tab" data-market-scope="mine">My listings</button>
        </div>
      </div>
      <div class="market-filters">
        <select id="market-slot" aria-label="Filter by slot">${options(SLOTS, "All slots")}</select>
        <select id="market-rarity" aria-label="Filter by rarity">${options(RARITIES, "All rarities")}</select>
        <p class="market-hint">Prices are set by players. Arrows compare with your equipped gear.</p>
      </div>
      <div class="market-listings" id="market-listings"></div>
    </section>`;
}

function listingCard(listing: ListingRead, mine: boolean): string {
  const { item } = listing;
  const rarity = item.definition.rarity;
  const busy = busyId === listing.id;
  const equipped = uiContext.equippedBySlot.get(item.definition.slot);
  const affordable = uiContext.balance >= listing.price;
  const bargain = listing.price < item.sell_price;
  const tip = itemTip(item, equipped ? `<div class="tip-sub">Compared with equipped ${escapeHtml(equipped.definition.name)}</div>` : "");
  const button = mine
    ? `<button type="button" class="ghost-button" data-market-action="cancel" data-listing-id="${listing.id}" ${busy ? "disabled" : ""}>${busy ? "Working…" : "Cancel"}</button>`
    : `<button type="button" class="primary-button" data-market-action="buy" data-listing-id="${listing.id}"
        ${busy || !affordable ? "disabled" : ""} ${affordable ? "" : tipAttr(`Need ${listing.price - uiContext.balance} more coins`)}>
        ${busy ? "Working…" : "Buy"}</button>`;
  return `
    <article class="listing-card rarity-card-${rarity}" ${tipAttr(tip)}>
      <div class="inventory-card-top">
        <span class="slot-icon">${slotIcon(item.definition.slot)}</span>
        <div>
          <strong class="rarity-${rarity}">${escapeHtml(item.definition.name)}</strong>
          <span>${item.definition.slot} · ${rarity}</span>
        </div>
      </div>
      <div class="stat-chips">${statChips(item, mine ? undefined : equipped)}</div>
      <p class="listing-seller">${mine ? "Your listing" : `by ${escapeHtml(listing.seller_username)}`}${bargain && !mine ? ' · <span class="deal">below quick-sell</span>' : ""}</p>
      <div class="listing-foot">
        <span class="price-tag ${affordable || mine ? "" : "unaffordable"}"><span class="coin-dot" aria-hidden="true"></span>${listing.price}</span>
        ${button}
      </div>
    </article>`;
}

export async function refreshMyListings(): Promise<void> {
  const listings = await getListings("mine");
  myListings = new Map(listings.map((listing) => [listing.item.id, listing]));
}

export async function refreshMarketplace(root: HTMLElement): Promise<void> {
  const container = root.querySelector<HTMLElement>("#market-listings");
  if (!container) return;
  try {
    const filters = { slot: slotFilter, rarity: rarityFilter };
    const [shown] = await Promise.all([getListings(scope, filters), refreshMyListings()]);
    container.innerHTML = shown.length
      ? shown.map((listing) => listingCard(listing, scope === "mine")).join("")
      : `<p class="empty-message">${scope === "mine" ? "You have nothing listed. Use List on a backpack item." : "No listings match. Check back soon."}</p>`;
  } catch (error) {
    container.innerHTML = "";
    toast(error instanceof Error ? error.message : "Could not load listings.", "error");
  }
}

export function mountMarketplace(root: HTMLElement, onInventoryChange: () => Promise<void>): void {
  const reload = async (): Promise<void> => {
    await onInventoryChange();
    await refreshMarketplace(root);
  };

  root.addEventListener("change", (event) => {
    const target = event.target as HTMLElement;
    if (target.id === "market-slot") slotFilter = (target as HTMLSelectElement).value;
    else if (target.id === "market-rarity") rarityFilter = (target as HTMLSelectElement).value;
    else return;
    void refreshMarketplace(root);
  });

  root.addEventListener("click", async (event) => {
    const target = event.target as HTMLElement;

    const scopeButton = target.closest<HTMLButtonElement>("[data-market-scope]");
    if (scopeButton) {
      scope = scopeButton.dataset.marketScope === "mine" ? "mine" : "others";
      root.querySelectorAll("[data-market-scope]").forEach((button) => {
        button.classList.toggle("active", button === scopeButton);
      });
            await refreshMarketplace(root);
      return;
    }

    const modeButton = target.closest<HTMLButtonElement>("[data-card-mode]");
    if (modeButton) {
      const card = modeButton.closest<HTMLElement>(".inventory-card");
      if (card) {
        card.dataset.cardState = modeButton.dataset.cardMode ?? "";
        if (card.dataset.cardState === "list") card.querySelector<HTMLInputElement>("input")?.select();
      }
      return;
    }

    const sellButton = target.closest<HTMLButtonElement>("[data-sell-confirm]");
    if (sellButton?.dataset.itemId) {
      sellButton.disabled = true;
      sellButton.textContent = "Selling…";
      try {
        const sale = await sellItem(sellButton.dataset.itemId);
        toast(`Sold ${sale.item_name} for ${sale.price} coins.`, "ok");
      } catch (error) {
        toast(error instanceof Error ? error.message : "Could not sell item.", "error");
      }
      await reload();
      return;
    }

    const confirmList = target.closest<HTMLButtonElement>("[data-list-confirm]");
    if (confirmList?.dataset.itemId) {
      const input = confirmList.closest(".card-sub")?.querySelector<HTMLInputElement>("input");
      const price = Number(input?.value);
      if (!Number.isInteger(price) || price <= 0 || price > 1_000_000) {
        toast("Enter a whole-number price between 1 and 1,000,000.", "error");
        return;
      }
      confirmList.disabled = true;
      confirmList.textContent = "Listing…";
      try {
        await createListing(confirmList.dataset.itemId, price);
        toast(`Listed for ${price} coins.`, "ok");
      } catch (error) {
        toast(error instanceof Error ? error.message : "Could not list item.", "error");
      }
      await reload();
      return;
    }

    const cancelInventory = target.closest<HTMLButtonElement>("[data-cancel-listing]");
    const marketButton = target.closest<HTMLButtonElement>("[data-market-action]");
    const listingId = cancelInventory?.dataset.cancelListing ?? marketButton?.dataset.listingId;
    if (!listingId) return;

    const buying = marketButton?.dataset.marketAction === "buy";
    if (buying && marketButton && marketButton.dataset.armed !== "1") {
      marketButton.dataset.armed = "1";
      marketButton.textContent = "Confirm?";
      marketButton.classList.add("is-armed");
      window.setTimeout(() => {
        if (marketButton.isConnected && marketButton.dataset.armed === "1") {
          marketButton.dataset.armed = "";
          marketButton.textContent = "Buy";
          marketButton.classList.remove("is-armed");
        }
      }, 3000);
      return;
    }

    busyId = listingId;
    await refreshMarketplace(root);
    try {
      if (buying) {
        const bought = await purchaseListing(listingId);
        toast(`Bought ${bought.item.definition.name} for ${bought.price} coins.`, "ok");
      } else {
        await cancelListing(listingId);
        toast("Listing cancelled. The item is back in your backpack.", "ok");
      }
    } catch (error) {
      toast(error instanceof Error ? error.message : "Marketplace action failed.", "error");
    } finally {
      busyId = null;
      await reload();
    }
  });
}
