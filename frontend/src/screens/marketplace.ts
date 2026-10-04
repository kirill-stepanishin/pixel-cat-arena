import {
  cancelListing,
  createListing,
  getListings,
  purchaseListing,
  type ListingScope,
} from "../api/gameApi";
import type { ListingRead } from "../types";

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

function escapeHtml(value: string): string {
  return value.replace(/[&<>"']/g, (char) => (
    { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[char] as string
  ));
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
        <p class="market-message" id="market-message" aria-live="polite"></p>
      </div>
      <div class="market-listings" id="market-listings"></div>
    </section>`;
}

function listingCard(listing: ListingRead, mine: boolean): string {
  const { item } = listing;
  const rarity = item.definition.rarity;
  const busy = busyId === listing.id;
  return `
    <article class="listing-card rarity-card-${rarity}">
      <div class="listing-head">
        <strong class="rarity-${rarity}">${escapeHtml(item.definition.name)}</strong>
        <span>${item.definition.slot} · ${rarity}</span>
      </div>
      <div class="inventory-card-meta">
        <small>ATK ${item.modifiers.attack || 0}</small>
        <small>DEF ${item.modifiers.defense || 0}</small>
        <small>SPD ${item.modifiers.speed || 0}</small>
      </div>
      <p class="listing-seller">${mine ? "Your listing" : `by ${escapeHtml(listing.seller_username)}`}</p>
      <div class="listing-foot">
        <span class="price-tag"><span class="coin-dot" aria-hidden="true"></span>${listing.price}</span>
        <button type="button" class="${mine ? "ghost-button" : "primary-button"}"
          data-market-action="${mine ? "cancel" : "buy"}" data-listing-id="${listing.id}" ${busy ? "disabled" : ""}>
          ${busy ? "Working…" : mine ? "Cancel" : "Buy"}
        </button>
      </div>
    </article>`;
}

function setMessage(root: HTMLElement, text: string, tone: "ok" | "error" | "" = ""): void {
  const message = root.querySelector<HTMLElement>("#market-message");
  if (!message) return;
  message.textContent = text;
  message.dataset.tone = tone;
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
    setMessage(root, error instanceof Error ? error.message : "Could not load listings.", "error");
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
      setMessage(root, "");
      await refreshMarketplace(root);
      return;
    }

    const openList = target.closest<HTMLButtonElement>("[data-list-toggle]");
    if (openList) {
      const row = openList.closest(".inventory-card")?.querySelector<HTMLElement>(".list-row");
      if (row) {
        row.hidden = !row.hidden;
        if (!row.hidden) row.querySelector<HTMLInputElement>("input")?.focus();
      }
      return;
    }

    const confirmList = target.closest<HTMLButtonElement>("[data-list-confirm]");
    if (confirmList?.dataset.itemId) {
      const input = confirmList.parentElement?.querySelector<HTMLInputElement>("input");
      const price = Number(input?.value);
      if (!Number.isInteger(price) || price <= 0) {
        setMessage(root, "Enter a whole-number price above 0.", "error");
        return;
      }
      confirmList.disabled = true;
      try {
        await createListing(confirmList.dataset.itemId, price);
        setMessage(root, `Listed for ${price} coins.`, "ok");
        await reload();
      } catch (error) {
        confirmList.disabled = false;
        setMessage(root, error instanceof Error ? error.message : "Could not list item.", "error");
      }
      return;
    }

    const cancelInventory = target.closest<HTMLButtonElement>("[data-cancel-listing]");
    const marketButton = target.closest<HTMLButtonElement>("[data-market-action]");
    const listingId = cancelInventory?.dataset.cancelListing ?? marketButton?.dataset.listingId;
    if (!listingId) return;

    const buying = marketButton?.dataset.marketAction === "buy";
    busyId = listingId;
    await refreshMarketplace(root);
    try {
      if (buying) {
        const bought = await purchaseListing(listingId);
        setMessage(root, `Bought ${bought.item.definition.name} for ${bought.price} coins.`, "ok");
      } else {
        await cancelListing(listingId);
        setMessage(root, "Listing cancelled. The item is back in your backpack.", "ok");
      }
    } catch (error) {
      setMessage(root, error instanceof Error ? error.message : "Marketplace action failed.", "error");
    } finally {
      busyId = null;
      await reload();
    }
  });
}
