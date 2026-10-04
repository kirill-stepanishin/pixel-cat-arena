import {
  ensureDevPlayer,
  equipItem,
  fightPve,
  getEnemyProgress,
  getInventory,
  unequipItem,
} from "../api/gameApi";
import { renderGlyph } from "../rendering/placeholders";
import { getEquippedItemsForCat, SLOT_ORDER, sumBonusForStat } from "../state/playerState";
import type {
  BattleRead,
  EnemyProgressRead,
  ItemInstanceRead,
  PlayerWithDetails,
  SlotKey,
  StatKey,
} from "../types";

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
          <span class="player-tag" id="player-tag">Connecting to arena…</span>
        </div>
      </header>

      <section class="panel battle-panel">
        <div class="panel-header compact">
          <div>
            <p class="eyebrow">ARENA</p>
            <h2>Cat versus cat</h2>
          </div>
          <span class="rarity-badge">Automatic PvE</span>
        </div>
        <div class="battle-arena">
          <div class="fighter fighter-player">
            <div class="fighter-label">
              <span class="eyebrow">YOUR CAT</span>
              <h3 id="cat-name">Mochi</h3>
            </div>
            <div class="cat-avatar" aria-hidden="true">ฅ^•ﻌ•^ฅ</div>
          </div>
          <div class="versus-badge">VS</div>
          <div class="fighter fighter-enemy">
            <div class="fighter-label">
              <span class="eyebrow">OPPONENT</span>
              <h3 id="enemy-name">Loading enemy…</h3>
              <select id="enemy-selector" class="enemy-selector" aria-label="Choose defeated enemy"></select>
            </div>
            <div class="enemy-body" aria-hidden="true">ฅ◉ﻌ◉ฅ</div>
          </div>
        </div>
        <div class="battle-controls">
          <ul class="enemy-stats">
            <li id="enemy-attack">ATK --</li>
            <li id="enemy-defense">DEF --</li>
            <li id="enemy-speed">SPD --</li>
          </ul>
          <div class="health-bars" aria-live="polite">
            <div><span>YOU</span><progress id="player-hp" max="100" value="100"></progress></div>
            <div><span>ENEMY</span><progress id="enemy-hp" max="100" value="100"></progress></div>
          </div>
          <button type="button" class="primary-button fight-button" data-action="fight">Fight</button>
          <button type="button" class="ghost-button skip-button" data-action="skip-battle" hidden>Skip to result</button>
          <div id="battle-playout" class="battle-playout" aria-live="polite"></div>
          <div id="battle-result" class="battle-result" aria-live="polite"></div>
          <div id="battle-reward" class="battle-reward" aria-live="polite"></div>
        </div>
      </section>

      <div class="dashboard-grid">
        <section class="panel hero-panel">
          <div class="panel-header">
            <div>
              <p class="eyebrow">CAT PAGE</p>
              <h2>Build your cat</h2>
            </div>
            <span class="rarity-badge" id="coins-badge">Coins: --</span>
          </div>

          <div class="cat-loadout">
            <div class="cat-stage" aria-label="Cat preview area">
              <div class="cat-avatar" aria-hidden="true">ฅ^•ﻌ•^ฅ</div>
              <div class="stat-grid" id="stat-grid"></div>
            </div>
            <div class="equipment-column">
              <p class="eyebrow">EQUIPMENT</p>
              <div id="equipment-slots" class="equipment-grid"></div>
            </div>
          </div>

          <div id="dashboard-error" class="error-message" aria-live="polite"></div>
        </section>

        <div class="right-column">
          <section class="panel inventory-panel">
            <div class="panel-header compact">
              <div>
                <p class="eyebrow">INVENTORY</p>
                <h3>Backpack</h3>
              </div>
            </div>
            <div id="inventory-list" class="inventory-list"></div>
          </section>

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
        </div>
      </div>
    </main>
  `;

  let pendingActionId: string | null = null;
  let skipPlayback: (() => void) | null = null;

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

    if (action === "skip-battle") {
      skipPlayback?.();
      return;
    }

    if (action === "fight") {
      const player = await ensureDevPlayer();
      const selector = root.querySelector<HTMLSelectElement>("#enemy-selector");
      setFightButtonState(root, true);
      try {
        const selectedStage = selector ? Number(selector.value) : undefined;
        const battle = await fightPve(player.id, Number.isFinite(selectedStage) ? selectedStage : undefined);
        const playback = createBattlePlayback(root, battle);
        skipPlayback = playback.skip;
        await playback.promise;
        skipPlayback = null;
        showBattleResult(root, battle.result);
        showBattleReward(root, battle);
        await refreshDashboard(root, null);
        setFightButtonState(root, false);
      } catch (error) {
        skipPlayback = null;
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
  const playerTagElement = root.querySelector<HTMLElement>("#player-tag");

  try {
    const player = await ensureDevPlayer();
    const [inventory, enemyProgress] = await Promise.all([
      getInventory(player.id),
      getEnemyProgress(player.id),
    ]);

    renderPlayerView(root, player, inventory, enemyProgress, pendingActionId);

    if (playerTagElement) {
      playerTagElement.textContent = `Player ${player.username}`;
    }
  } catch (error) {
    showError(root, error instanceof Error ? error.message : "Unable to load the dev player.");

    if (playerTagElement) {
      playerTagElement.textContent = "Need backend";
    }
  }
}

function renderPlayerView(
  root: HTMLElement,
  player: PlayerWithDetails,
  inventory: ItemInstanceRead[],
  enemyProgress: EnemyProgressRead,
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

  const currentEnemy = enemyProgress.enemies.find((enemy) => enemy.stage === enemyProgress.selected_stage)
    ?? enemyProgress.enemies[enemyProgress.enemies.length - 1];
  if (enemyName) enemyName.textContent = currentEnemy?.name ?? "No enemy yet";
  if (enemyAttack) enemyAttack.textContent = `ATK ${currentEnemy?.attack ?? "--"}`;
  if (enemyDefense) enemyDefense.textContent = `DEF ${currentEnemy?.defense ?? "--"}`;
  if (enemySpeed) enemySpeed.textContent = `SPD ${currentEnemy?.speed ?? "--"}`;
  renderEnemySelector(root, enemyProgress);

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

function renderEnemySelector(root: HTMLElement, progress: EnemyProgressRead): void {
  const selector = root.querySelector<HTMLSelectElement>("#enemy-selector");
  if (!selector) return;

  selector.innerHTML = progress.enemies.map((enemy) =>
    `<option value="${enemy.stage}" ${enemy.stage === progress.selected_stage ? "selected" : ""}>${enemy.name}</option>`
  ).join("");
}

function createBattlePlayback(root: HTMLElement, battle: BattleRead): {
  promise: Promise<void>;
  skip: () => void;
} {
  const playerHp = root.querySelector<HTMLProgressElement>("#player-hp");
  const enemyHp = root.querySelector<HTMLProgressElement>("#enemy-hp");
  const playout = root.querySelector<HTMLElement>("#battle-playout");
  const skipButton = root.querySelector<HTMLButtonElement>('[data-action="skip-battle"]');
  let resolvePlayback: (() => void) | null = null;
  let timer: number | undefined;
  let skipped = false;

  if (playerHp) playerHp.value = battle.player_snapshot.max_hp;
  if (enemyHp) enemyHp.value = battle.enemy_snapshot.max_hp;
  if (playout) playout.textContent = "Battle started…";
  if (skipButton) skipButton.hidden = false;

  const finish = (): void => {
    if (timer !== undefined) window.clearTimeout(timer);
    if (playerHp) playerHp.value = battle.events.at(-1)?.player_hp ?? playerHp.value;
    if (enemyHp) enemyHp.value = battle.events.at(-1)?.enemy_hp ?? enemyHp.value;
    if (playout) playout.textContent = "Battle complete.";
    if (skipButton) skipButton.hidden = true;
    resolvePlayback?.();
    resolvePlayback = null;
  };

  const promise = new Promise<void>((resolve) => {
    resolvePlayback = resolve;
    let index = 0;
    const playNext = (): void => {
      if (skipped || index >= battle.events.length) {
        finish();
        return;
      }
      const event = battle.events[index++];
      if (playerHp) playerHp.value = event.player_hp;
      if (enemyHp) enemyHp.value = event.enemy_hp;
      if (playout) {
        playout.textContent = event.event_type === "attack"
          ? `${event.attacker === "player" ? "Mochi" : battle.enemy_snapshot.name} attacks for ${event.damage}!`
          : event.event_type === "draw" ? "Time! It’s a draw." : event.event_type === "victory" ? "Victory blow!" : "Defeat blow!";
      }
      timer = window.setTimeout(playNext, 180);
    };
    playNext();
  });

  return {
    promise,
    skip: () => {
      skipped = true;
      finish();
    },
  };
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

function showBattleReward(root: HTMLElement, battle: BattleRead): void {
  const rewardElement = root.querySelector<HTMLElement>("#battle-reward");
  if (!rewardElement) return;
  if (!battle.reward) {
    rewardElement.textContent = "No reward this time.";
    return;
  }
  rewardElement.textContent = battle.reward.item_instance_id
    ? `Reward: +${battle.reward.currency_amount} coins and a new item!`
    : `Reward: +${battle.reward.currency_amount} coins`;
}

function setFightButtonState(root: HTMLElement, pending: boolean): void {
  const fightButton = root.querySelector<HTMLButtonElement>('[data-action="fight"]');
  if (!fightButton) return;

  fightButton.disabled = pending;
  fightButton.textContent = pending ? "Fighting…" : "Fight";
}
