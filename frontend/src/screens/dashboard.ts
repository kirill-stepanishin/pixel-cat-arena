import {
  ensureDevPlayer,
  equipItem,
  fightPve,
  getCurrentEnemy,
  getInventory,
  unequipItem,
} from "../api/gameApi";
import { renderGlyph } from "../rendering/placeholders";
import { getEquippedItemsForCat, SLOT_ORDER, sumBonusForStat } from "../state/playerState";
import type { EnemyRead, ItemInstanceRead, PlayerWithDetails, SlotKey, StatKey } from "../types";

const STAT_ORDER: Array<{ key: StatKey; label: string }> = [
  { key: "attack", label: "ATK" },
  { key: "defense", label: "DEF" },
  { key: "speed", label: "SPD" },
];

export function mountDashboard(root: HTMLElement): void {
  root.innerHTML = `
    <main class="shell">
      <header class="topbar">
        <div>
          <p class="eyebrow">PIXEL CAT ARENA</p>
          <h1>Build. Battle. Trade.</h1>
        </div>
        <div class="topbar-meta">
          <span class="status" id="api-status">Loading save…</span>
          <span class="player-tag" id="player-tag">Connecting to arena…</span>
        </div>
      </header>

      <div class="dashboard-grid">
        <section class="panel hero-panel">
          <div class="panel-header">
            <div>
              <p class="eyebrow">STARTER CAT</p>
              <h2 id="cat-name">Mochi</h2>
            </div>
            <span class="rarity-badge" id="coins-badge">Coins: --</span>
          </div>

          <div class="cat-stage" aria-label="Cat preview area">
            <div class="cat-avatar" aria-hidden="true">ฅ^•ﻌ•^ฅ</div>
          </div>

          <div class="stat-grid" id="stat-grid"></div>
          <div id="dashboard-error" class="error-message" aria-live="polite"></div>
        </section>

        <section class="panel equipment-panel">
          <div class="panel-header compact">
            <div>
              <p class="eyebrow">EQUIPMENT</p>
              <h3>Loadout</h3>
            </div>
          </div>
          <div id="equipment-slots" class="equipment-grid"></div>
        </section>

        <section class="panel inventory-panel">
          <div class="panel-header compact">
            <div>
              <p class="eyebrow">INVENTORY</p>
              <h3>Backpack</h3>
            </div>
          </div>
          <div id="inventory-list" class="inventory-list"></div>
        </section>

        <aside class="panel preview-panel">
          <div class="panel-header compact">
            <div>
              <p class="eyebrow">ENEMY</p>
              <h3 id="enemy-name">Loading enemy…</h3>
            </div>
          </div>
          <div class="enemy-figure" aria-hidden="true">
            <div class="enemy-body">◉</div>
          </div>
          <ul class="enemy-stats">
            <li id="enemy-attack">ATK --</li>
            <li id="enemy-defense">DEF --</li>
            <li id="enemy-speed">SPD --</li>
          </ul>
          <button type="button" class="primary-button fight-button" data-action="fight">Fight</button>
          <div id="battle-result" class="battle-result" aria-live="polite"></div>
        </aside>
      </div>

      <section class="panel marketplace-panel">
        <div class="panel-header compact">
          <div>
            <p class="eyebrow">MARKETPLACE</p>
            <h3>Coming soon</h3>
          </div>
        </div>
        <div class="market-grid">
          <div class="market-card">
            <span class="market-label">Tier</span>
            <strong>Starter gear</strong>
          </div>
          <div class="market-card">
            <span class="market-label">Market</span>
            <strong>Live listings</strong>
          </div>
          <div class="market-card">
            <span class="market-label">Next phase</span>
            <strong>Trade and PvP</strong>
          </div>
        </div>
      </section>
    </main>
  `;

  let pendingActionId: string | null = null;

  root.addEventListener("click", async (event) => {
    const target = event.target as HTMLElement;
    const actionButton = target.closest<HTMLButtonElement>("[data-action]");

    if (!actionButton) {
      return;
    }

    const { action, itemId, playerId, catId } = actionButton.dataset;

    if (!action) {
      return;
    }

    if (action === "fight") {
      const player = await ensureDevPlayer();
      setFightButtonState(root, true);
      try {
        const battle = await fightPve(player.id);
        showBattleResult(root, battle.result);
        await refreshDashboard(root, null);
        setFightButtonState(root, false);
      } catch (error) {
        showError(root, error instanceof Error ? error.message : "Could not start battle.");
        setFightButtonState(root, false);
      }
      return;
    }

    if (!itemId || !playerId || !catId) {
      return;
    }

    pendingActionId = itemId;
    await refreshDashboard(root, pendingActionId);

    try {
      if (action === "equip") {
        await equipItem(playerId, catId, itemId);
      } else if (action === "unequip") {
        await unequipItem(playerId, catId, itemId);
      }

      pendingActionId = null;
      await refreshDashboard(root, null);
    } catch (error) {
      pendingActionId = null;
      showError(root, error instanceof Error ? error.message : "Could not update equipment.");
      await refreshDashboard(root, null);
    }
  });

  void refreshDashboard(root, null);
}

async function refreshDashboard(root: HTMLElement, pendingActionId: string | null): Promise<void> {
  const statusElement = root.querySelector<HTMLElement>("#api-status");
  const playerTagElement = root.querySelector<HTMLElement>("#player-tag");

  if (statusElement) {
    statusElement.textContent = "Loading save…";
    statusElement.dataset.connected = "true";
  }

  try {
    const player = await ensureDevPlayer();
    const [inventory, currentEnemy] = await Promise.all([
      getInventory(player.id),
      getCurrentEnemy(player.id),
    ]);

    renderPlayerView(root, player, inventory, currentEnemy, pendingActionId);

    if (playerTagElement) {
      playerTagElement.textContent = `Player ${player.username}`;
    }

    if (statusElement) {
      statusElement.textContent = "API online";
      statusElement.dataset.connected = "true";
    }
  } catch (error) {
    showError(root, error instanceof Error ? error.message : "Unable to load the dev player.");

    if (statusElement) {
      statusElement.textContent = "API offline";
      statusElement.dataset.connected = "false";
    }

    if (playerTagElement) {
      playerTagElement.textContent = "Need backend";
    }
  }
}

function renderPlayerView(
  root: HTMLElement,
  player: PlayerWithDetails,
  inventory: ItemInstanceRead[],
  currentEnemy: EnemyRead,
  pendingActionId: string | null,
): void {
  const cat = player.cats[0] ?? null;
  const money = player.currencies[0]?.balance ?? 0;
  const statGrid = root.querySelector<HTMLElement>("#stat-grid");
  const catNameElement = root.querySelector<HTMLElement>("#cat-name");
  const coinsBadge = root.querySelector<HTMLElement>("#coins-badge");
  const enemyName = root.querySelector<HTMLElement>("#enemy-name");
  const enemyAttack = root.querySelector<HTMLElement>("#enemy-attack");
  const enemyDefense = root.querySelector<HTMLElement>("#enemy-defense");
  const enemySpeed = root.querySelector<HTMLElement>("#enemy-speed");

  if (enemyName) enemyName.textContent = currentEnemy.name;
  if (enemyAttack) enemyAttack.textContent = `ATK ${currentEnemy.attack}`;
  if (enemyDefense) enemyDefense.textContent = `DEF ${currentEnemy.defense}`;
  if (enemySpeed) enemySpeed.textContent = `SPD ${currentEnemy.speed}`;

  if (catNameElement) {
    catNameElement.textContent = cat?.name ?? "No cat yet";
  }

  if (coinsBadge) {
    coinsBadge.textContent = `Coins: ${money}`;
  }

  if (!cat) {
    if (statGrid) {
      statGrid.innerHTML = '<p class="empty-message">No cat was returned by the server.</p>';
    }
    renderEquipmentSlots(root, [], pendingActionId);
    renderInventoryList(root, player.id, null, [], pendingActionId);
    return;
  }

  const equippedItems = getEquippedItemsForCat(inventory, cat.id);
  const bonusTotals = {
    attack: sumBonusForStat(equippedItems, "attack"),
    defense: sumBonusForStat(equippedItems, "defense"),
    speed: sumBonusForStat(equippedItems, "speed"),
  };

  const totals = {
    attack: cat.attack + bonusTotals.attack,
    defense: cat.defense + bonusTotals.defense,
    speed: cat.speed + bonusTotals.speed,
  };

  if (statGrid) {
    statGrid.innerHTML = STAT_ORDER.map((stat) => {
      const total = totals[stat.key];
      const bonus = bonusTotals[stat.key];
      const formattedBonus = bonus >= 0 ? `(+${bonus})` : `(${bonus})`;
      return `
        <div class="stat-card">
          <span>${stat.label}</span>
          <strong>${total}</strong>
          <small>${formattedBonus}</small>
        </div>
      `;
    }).join("");
  }

  renderEquipmentSlots(root, equippedItems, pendingActionId);
  renderInventoryList(root, player.id, cat, inventory, pendingActionId);
}

function renderEquipmentSlots(
  root: HTMLElement,
  equippedItems: ItemInstanceRead[],
  pendingActionId: string | null,
): void {
  const equipmentSlotsElement = root.querySelector<HTMLElement>("#equipment-slots");

  if (!equipmentSlotsElement) {
    return;
  }

  const itemBySlot = new Map<SlotKey, ItemInstanceRead | undefined>();
  SLOT_ORDER.forEach((slot) => {
    itemBySlot.set(slot, equippedItems.find((item) => item.definition.slot === slot));
  });

  equipmentSlotsElement.innerHTML = SLOT_ORDER.map((slot) => {
    const item = itemBySlot.get(slot);
    const itemName = item?.definition.name ?? "Empty slot";
    const labelText = item ? item.definition.slot.toUpperCase() : slot.toUpperCase();
    const buttonMarkup = item
      ? `
        <button type="button" class="ghost-button" data-action="unequip" data-item-id="${item.id}" data-player-id="${item.owner_id}" data-cat-id="${item.equipped_cat_id ?? ""}">
          ${pendingActionId === item.id ? "Updating…" : "Unequip"}
        </button>
      `
      : `<span class="empty-slot">No gear equipped</span>`;

    return `
      <div class="equipment-slot">
        <div class="equipment-headline">
          <span>${labelText}</span>
          <span class="slot-badge">${item?.definition.rarity ?? "empty"}</span>
        </div>
        <div class="equipment-visual">${item ? renderGlyph(item.definition.visual_key) : "□"}</div>
        <strong>${itemName}</strong>
        ${buttonMarkup}
      </div>
    `;
  }).join("");
}

function renderInventoryList(
  root: HTMLElement,
  playerId: string,
  cat: { id: string } | null,
  inventory: ItemInstanceRead[],
  pendingActionId: string | null,
): void {
  const inventoryList = root.querySelector<HTMLElement>("#inventory-list");

  if (!inventoryList) {
    return;
  }

  if (!inventory.length) {
    inventoryList.innerHTML = '<p class="empty-message">No gear in the backpack yet.</p>';
    return;
  }

  const unequippedItems = inventory.filter((item) => !(cat && item.equipped_cat_id === cat.id));
  const visibleItems = cat ? unequippedItems : inventory;

  if (!visibleItems.length) {
    inventoryList.innerHTML = '<p class="empty-message">Everything is equipped. Your cat is ready.</p>';
    return;
  }

  inventoryList.innerHTML = visibleItems.map((item) => {
    const isEquipped = item.equipped_cat_id === cat?.id;
    const buttonText = isEquipped ? "Unequip" : "Equip";
    const action = isEquipped ? "unequip" : "equip";

    return `
      <article class="inventory-card">
        <div class="inventory-card-top">
          <div class="mini-visual">${renderGlyph(item.definition.visual_key)}</div>
          <div>
            <strong>${item.definition.name}</strong>
            <span>${item.definition.slot} • ${item.definition.rarity}</span>
          </div>
        </div>
        <div class="inventory-card-meta">
          <small>ATK ${item.definition.modifiers.attack || 0}</small>
          <small>DEF ${item.definition.modifiers.defense || 0}</small>
          <small>SPD ${item.definition.modifiers.speed || 0}</small>
        </div>
        <button
          type="button"
          class="primary-button"
          data-action="${action}"
          data-item-id="${item.id}"
          data-player-id="${playerId}"
          data-cat-id="${cat?.id ?? ""}"
          ${pendingActionId === item.id ? "disabled" : ""}
          ${!cat ? "disabled" : ""}
        >
          ${pendingActionId === item.id ? "Updating…" : buttonText}
        </button>
      </article>
    `;
  }).join("");
}

function showError(root: HTMLElement, message: string): void {
  const errorElement = root.querySelector<HTMLElement>("#dashboard-error");

  if (errorElement) {
    errorElement.textContent = message;
  }
}

function showBattleResult(root: HTMLElement, result: "player" | "enemy" | "draw"): void {
  const resultElement = root.querySelector<HTMLElement>("#battle-result");
  if (!resultElement) return;
  resultElement.textContent =
    result === "player" ? "Victory! The next dummy is ready." :
    result === "enemy" ? "Defeat. Try again against the same dummy." :
    "Draw. The current dummy remains.";
  resultElement.dataset.result = result;
}

function setFightButtonState(root: HTMLElement, pending: boolean): void {
  const fightButton = root.querySelector<HTMLButtonElement>('[data-action="fight"]');
  if (!fightButton) return;

  fightButton.disabled = pending;
  fightButton.textContent = pending ? "Fighting…" : "Fight";
}
