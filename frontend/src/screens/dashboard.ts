import {
  equipItem,
  fightPve,
  getEnemyProgress,
  getInventory,
  unequipItem,
  publishBuild,
  challengePlayer,
  resolveChallenge,
} from "../api/gameApi";
import { getCurrentPlayer, logout } from "../api/authApi";
import { getListedItem, marketplaceMarkup, mountMarketplace, refreshMarketplace, refreshMyListings } from "./marketplace";
import { renderCat } from "../rendering/placeholders";
import { getEquippedItemsForCat, SLOT_ORDER, sumBonusForStat } from "../state/playerState";
import type {
  BattleRead,
  EnemyProgressRead,
  ItemInstanceRead,
  PlayerWithDetails,
  BuildSnapshotRead,
  PvpMatchRead,
  SlotKey,
  StatKey,
} from "../types";


const STAT_ORDER: Array<{ key: StatKey; label: string }> = [
  { key: "attack", label: "ATK" },
  { key: "defense", label: "DEF" },
  { key: "speed", label: "SPD" },
];

function rarityClass(rarity: ItemInstanceRead["definition"]["rarity"]): string {
  return `rarity-${rarity}`;
}

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
          <button type="button" class="ghost-button" id="logout-button">Log out</button>
        </div>
      </header>

      <section class="panel battle-panel">
        <div class="panel-header compact">
          <div>
            <p class="eyebrow">ARENA</p>
            <h2>Cat versus cat</h2>
          </div>
          <div class="mode-tabs" role="tablist">
            <button type="button" class="mode-tab active" data-mode="pve">PvE</button>
            <button type="button" class="mode-tab" data-mode="pvp">Async PvP</button>
          </div>
        </div>
        <div class="battle-arena">
          <ul class="arena-stats arena-stats-player" id="player-arena-stats">
            <li>ATK --</li>
            <li>DEF --</li>
            <li>SPD --</li>
          </ul>
          <div class="fighter fighter-player">
            <div class="fighter-label">
              <span class="eyebrow">YOUR CAT</span>
              <h3 id="cat-name">Mochi</h3>
            </div>
            <div class="fighter-core">
              <div class="fighter-health fighter-health-player">
                <span>YOU</span>
                <progress id="player-hp" max="100" value="100"></progress>
              </div>
              <div class="cat-avatar" aria-hidden="true">${renderCat()}</div>
            </div>
          </div>
          <div class="versus-badge">VS</div>
          <div class="fighter fighter-enemy">
            <div class="fighter-core">
              <div class="fighter-health fighter-health-enemy">
                <span id="opponent-kind">ENEMY</span>
                <progress id="enemy-hp" max="100" value="100"></progress>
              </div>
              <div class="enemy-body" aria-hidden="true">${renderCat(true)}</div>
            </div>
            <div class="fighter-label">
              <span class="eyebrow">OPPONENT</span>
              <h3 id="enemy-name">Loading opponent…</h3>
              <select id="enemy-selector" class="enemy-selector" aria-label="Choose defeated enemy"></select>
            </div>
          </div>
          <ul class="arena-stats arena-stats-enemy">
            <li id="enemy-attack">ATK --</li>
            <li id="enemy-defense">DEF --</li>
            <li id="enemy-speed">SPD --</li>
          </ul>
        </div>
        <div class="battle-feed">
          <p id="battle-playout" class="battle-ticker" aria-live="polite">Choose an opponent and press Fight.</p>
          <button type="button" class="ghost-button skip-button" data-action="skip-battle" hidden>Skip</button>
        </div>
        <div class="battle-controls" id="pve-controls">
          <div class="battle-action">
            <button type="button" class="primary-button fight-button" data-action="fight">Fight</button>
          </div>
        </div>
        <div class="pvp-controls is-hidden" id="pvp-panel">
          <div class="pvp-step">
            <div class="pvp-step-head"><span class="step-number">1</span>Publish your build</div>
            <button type="button" class="ghost-button" id="publish-build" data-label="Publish build">Publish build</button>
            <p class="step-caption" id="published-build-status">Not published yet</p>
          </div>
          <div class="pvp-step">
            <div class="pvp-step-head"><span class="step-number">2</span>Pick an opponent</div>
            <div class="input-group">
              <input id="challenge-username" placeholder="Opponent username" autocomplete="off" aria-label="Opponent username">
              <button type="button" class="ghost-button" id="challenge-player" data-label="Challenge">Challenge</button>
            </div>
            <p class="step-caption" id="challenge-status">They must publish a build too</p>
          </div>
          <div class="pvp-step">
            <div class="pvp-step-head"><span class="step-number">3</span>Fight</div>
            <button type="button" class="primary-button" id="resolve-challenge" data-label="Start match" disabled>Start match</button>
            <p class="step-caption" id="pvp-status">Create a challenge first</p>
          </div>
        </div>
        <div id="battle-summary" class="result-card" data-state="idle" aria-live="polite">
          <p class="result-idle">Battle results will appear here.</p>
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
              <div class="cat-avatar" aria-hidden="true">${renderCat()}</div>
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
        </div>
      </div>
      ${marketplaceMarkup()}
    </main>
  `;

  let pendingActionId: string | null = null;
  let skipPlayback: (() => void) | null = null;
  let arenaMode: "pve" | "pvp" = "pve";

  root.addEventListener("click", async (event) => {
    const target = event.target as HTMLElement;
    const actionButton = target.closest<HTMLButtonElement>("[data-action]");

    const modeButton = target.closest<HTMLButtonElement>("[data-mode]");
    if (modeButton) {
      arenaMode = modeButton.dataset.mode === "pvp" ? "pvp" : "pve";
      root.querySelectorAll("[data-mode]").forEach((button) => {
        button.classList.toggle("active", button === modeButton);
      });
      root.querySelector<HTMLElement>("#pvp-panel")?.classList.toggle("is-hidden", arenaMode !== "pvp");
      root.querySelector<HTMLElement>("#pve-controls")?.classList.toggle("is-hidden", arenaMode !== "pve");
      resetBattleSummary(root);
      const ticker = root.querySelector<HTMLElement>("#battle-playout");
      if (ticker) {
        ticker.textContent = arenaMode === "pve"
          ? "Choose an opponent and press Fight."
          : "Publish your build, then challenge another player.";
      }
      if (arenaMode === "pve") {
        const enemyBody = root.querySelector<HTMLElement>(".fighter-enemy .enemy-body");
        if (enemyBody) {
          enemyBody.innerHTML = renderCat(true);
          enemyBody.classList.remove("is-mirrored");
        }
        const kind = root.querySelector<HTMLElement>("#opponent-kind");
        if (kind) kind.textContent = "ENEMY";
        const selector = root.querySelector<HTMLSelectElement>("#enemy-selector");
        if (selector) selector.hidden = false;
        void refreshDashboard(root, null);
      }
      return;
    }

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
      const player = await getCurrentPlayer();
      const selector = root.querySelector<HTMLSelectElement>("#enemy-selector");
      setFightButtonState(root, true);
      try {
        const selectedStage = selector ? Number(selector.value) : undefined;
        const battle = await fightPve(player.id, Number.isFinite(selectedStage) ? selectedStage : undefined);
        const playback = createBattlePlayback(root, battle);
        skipPlayback = playback.skip;
        await playback.promise;
        skipPlayback = null;
        showPveSummary(root, battle);
        await refreshDashboard(root, null);
        if (battle.reward) bumpCoins(root);
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

  root.querySelector("#logout-button")?.addEventListener("click", async () => {
    await logout();
    window.location.reload();
  });
  root.querySelector("#publish-build")?.addEventListener("click", () => void pvpAction(root, "publish", (skip) => { skipPlayback = skip; }));
  root.querySelector("#challenge-player")?.addEventListener("click", () => void pvpAction(root, "challenge", (skip) => { skipPlayback = skip; }));
  root.querySelector("#resolve-challenge")?.addEventListener("click", () => void pvpAction(root, "resolve", (skip) => { skipPlayback = skip; }));

  mountMarketplace(root, () => refreshDashboard(root, null));
  void refreshDashboard(root, null).then(() => refreshMarketplace(root));
}

type CaptionTone = "ok" | "error" | "neutral";

function setCaption(element: HTMLElement | null, text: string, tone: CaptionTone = "neutral"): void {
  if (!element) return;
  element.textContent = text;
  element.title = text;
  element.dataset.tone = tone;
}

function setPvpBusy(root: HTMLElement, busyButtonId: string | null): void {
  root.querySelectorAll<HTMLButtonElement>("#pvp-panel button").forEach((button) => {
    const label = button.dataset.label ?? button.textContent ?? "";
    const busy = busyButtonId !== null;
    const isResolve = button.id === "resolve-challenge";
    button.disabled = busy || (isResolve && !button.dataset.challengeId);
    button.textContent = busy && button.id === busyButtonId ? "Working…" : label;
  });
}

async function pvpAction(
  root: HTMLElement,
  action: "publish" | "challenge" | "resolve",
  setSkip: (skip: (() => void) | null) => void,
): Promise<void> {
  const publishCaption = root.querySelector<HTMLElement>("#published-build-status");
  const challengeCaption = root.querySelector<HTMLElement>("#challenge-status");
  const matchCaption = root.querySelector<HTMLElement>("#pvp-status");
  const resolveButton = root.querySelector<HTMLButtonElement>("#resolve-challenge");
  const buttonId = { publish: "publish-build", challenge: "challenge-player", resolve: "resolve-challenge" }[action];
  const caption = { publish: publishCaption, challenge: challengeCaption, resolve: matchCaption }[action];

  setPvpBusy(root, buttonId);
  try {
    const player = await getCurrentPlayer();
    if (action === "publish") {
      const build = await publishBuild(player.id);
      setCaption(publishCaption, `Published v${build.version} ✓`, "ok");
    } else if (action === "challenge") {
      const username = root.querySelector<HTMLInputElement>("#challenge-username")?.value.trim();
      if (!username) throw new Error("Enter an opponent username.");
      const challenge = await challengePlayer(player.id, username);
      const opponentBuild = challenge.challenged_id === player.id
        ? challenge.challenger_build
        : challenge.challenged_build;
      resetBattleSummary(root);
      renderPvpOpponent(root, opponentBuild);
      if (resolveButton) {
        resolveButton.dataset.challengeId = challenge.id;
        resolveButton.dataset.opponent = username;
        resolveButton.dataset.label = "Start match";
      }
      setCaption(challengeCaption, `Challenge ready vs ${username}`, "ok");
      setCaption(matchCaption, "Press Start match", "neutral");
      const ticker = root.querySelector<HTMLElement>("#battle-playout");
      if (ticker) ticker.textContent = `${opponentBuild.cat.name} is waiting in the arena.`;
    } else {
      const challengeId = resolveButton?.dataset.challengeId;
      if (!challengeId) throw new Error("Create a challenge first.");
      const match = await resolveChallenge(challengeId);
      const playback = createBattlePlayback(root, toPvpReplay(match));
      setSkip(playback.skip);
      await playback.promise;
      setSkip(null);
      showPvpSummary(root, match, resolveButton?.dataset.opponent ?? "your opponent");
      setCaption(matchCaption, `Match complete · ${match.turn_count} turns`, "ok");
      if (resolveButton) resolveButton.dataset.label = "Watch again";
    }
  } catch (error) {
    setSkip(null);
    setCaption(caption, error instanceof Error ? error.message : "PvP action failed.", "error");
  } finally {
    setPvpBusy(root, null);
  }
}

function renderPvpOpponent(root: HTMLElement, build: BuildSnapshotRead): void {
  const name = root.querySelector<HTMLElement>("#enemy-name");
  const kind = root.querySelector<HTMLElement>("#opponent-kind");
  const attack = root.querySelector<HTMLElement>("#enemy-attack");
  const defense = root.querySelector<HTMLElement>("#enemy-defense");
  const speed = root.querySelector<HTMLElement>("#enemy-speed");
  const selector = root.querySelector<HTMLSelectElement>("#enemy-selector");
  if (name) name.textContent = build.cat.name;
  if (kind) kind.textContent = "PLAYER";
  if (attack) attack.textContent = `ATK ${build.cat.attack}`;
  if (defense) defense.textContent = `DEF ${build.cat.defense}`;
  if (speed) speed.textContent = `SPD ${build.cat.speed}`;
  if (selector) selector.hidden = true;
  const visuals = build.equipment
    .filter((item) => item.visual_key)
    .map((item) => ({ visualKey: item.visual_key!, slot: item.slot }));
  const enemyBody = root.querySelector<HTMLElement>(".fighter-enemy .enemy-body");
  if (enemyBody) {
    enemyBody.innerHTML = renderCat(false, visuals);
    enemyBody.classList.add("is-mirrored");
  }
}

function toPvpReplay(match: PvpMatchRead): BattleRead {
  return {
    id: match.id,
    enemy_stage: 0,
    result: match.result === "challenger" ? "player" : "enemy",
    events: match.events,
    player_snapshot: match.challenger_snapshot,
    enemy_snapshot: match.challenged_snapshot,
    reward: null,
  };
}

async function refreshDashboard(root: HTMLElement, pendingActionId: string | null): Promise<void> {
  const playerTagElement = root.querySelector<HTMLElement>("#player-tag");

  try {
    const player = await getCurrentPlayer();
    const [inventory, enemyProgress] = await Promise.all([
      getInventory(player.id),
      getEnemyProgress(player.id),
      refreshMyListings().catch(() => undefined),
    ]);

    renderPlayerView(root, player, inventory, enemyProgress, pendingActionId);

    if (playerTagElement) {
      playerTagElement.textContent = `Player ${player.username}`;
    }
  } catch (error) {
    showError(root, error instanceof Error ? error.message : "Unable to load the player.");

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

  const arenaStats = root.querySelector<HTMLElement>("#player-arena-stats");
  if (arenaStats) {
    arenaStats.innerHTML = STAT_ORDER.map(
      (stat) => `<li>${stat.label} ${totals[stat.key]}</li>`,
    ).join("");
  }

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
  const equippedVisuals = equippedItems.map((item) => ({
    visualKey: item.definition.visual_key,
    slot: item.definition.slot,
  }));
  const catMarkup = renderCat(false, equippedVisuals);
  const catAvatar = root.querySelector<HTMLElement>(".cat-stage .cat-avatar");
  const battleAvatar = root.querySelector<HTMLElement>(".fighter-player .cat-avatar");
  if (catAvatar) catAvatar.innerHTML = catMarkup;
  if (battleAvatar) battleAvatar.innerHTML = renderCat(false, equippedVisuals);
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

  if (playerHp) {
    playerHp.max = battle.player_snapshot.max_hp;
    playerHp.value = battle.player_snapshot.max_hp;
  }
  if (enemyHp) {
    enemyHp.max = battle.enemy_snapshot.max_hp;
    enemyHp.value = battle.enemy_snapshot.max_hp;
  }
  clearOutcomePose(root);
  if (playout) {
    playout.textContent = "Battle started…";
    delete playout.dataset.side;
  }
  if (skipButton) skipButton.hidden = false;

  const finish = (): void => {
    if (timer !== undefined) window.clearTimeout(timer);
    if (playerHp) playerHp.value = battle.events.at(-1)?.player_hp ?? playerHp.value;
    if (enemyHp) enemyHp.value = battle.events.at(-1)?.enemy_hp ?? enemyHp.value;
    if (playout) {
      playout.textContent = "Battle complete.";
      delete playout.dataset.side;
    }
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
      if (event.event_type === "attack" && event.attacker) {
        triggerAttackAnimation(root, event.attacker);
      }
      if (playout) {
        playout.textContent = event.event_type === "attack"
          ? `${event.attacker === "player" ? battle.player_snapshot.name : battle.enemy_snapshot.name} attacks for ${event.damage}!`
          : event.event_type === "victory" ? "Victory blow!" : "Defeat blow!";
        if (event.attacker) playout.dataset.side = event.attacker;
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

function triggerAttackAnimation(root: HTMLElement, attacker: "player" | "enemy"): void {
  const selector = attacker === "player"
    ? ".fighter-player .cat-avatar"
    : ".fighter-enemy .enemy-body";
  const sprite = root.querySelector<HTMLElement>(selector);
  if (!sprite) return;

  sprite.classList.remove("attack-lunge");
  void sprite.offsetWidth;
  sprite.classList.add("attack-lunge");
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
        </div>
        <strong class="${item ? rarityClass(item.definition.rarity) : ""}">${itemName}</strong>
        ${item ? `<span class="item-rarity ${rarityClass(item.definition.rarity)}">${item.definition.rarity}</span>` : ""}
        ${item ? `<div class="equipment-modifiers">${formatItemModifiers(item)}</div>` : ""}
        ${buttonMarkup}
      </div>
    `;
  }).join("");
}

function formatItemModifiers(item: ItemInstanceRead): string {
  const modifiers: Array<[string, number]> = [
    ["ATK", item.modifiers.attack],
    ["DEF", item.modifiers.defense],
    ["SPD", item.modifiers.speed],
  ];

  return modifiers
    .filter(([, value]) => value !== 0)
    .map(([label, value]) => `${label} ${value > 0 ? "+" : ""}${value}`)
    .join(" · ") || "No stat bonus";
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
    const listing = getListedItem(item.id);

    return `
      <article class="inventory-card ${rarityClass(item.definition.rarity)}">
        <div class="inventory-card-top">
          <div>
            <strong class="${rarityClass(item.definition.rarity)}">${item.definition.name}</strong>
            <span>${item.definition.slot}</span>
          </div>
        </div>
        <span class="item-rarity ${rarityClass(item.definition.rarity)}">${item.definition.rarity}</span>
        <div class="inventory-card-meta">
          <small>ATK ${item.modifiers.attack || 0}</small>
          <small>DEF ${item.modifiers.defense || 0}</small>
          <small>SPD ${item.modifiers.speed || 0}</small>
        </div>
        ${listing ? `<span class="listed-badge">Listed · ${listing.price} coins</span>
        <button type="button" class="ghost-button" data-cancel-listing="${listing.id}">Cancel listing</button>` : `
        <div class="card-actions">
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
          ${isEquipped ? "" : '<button type="button" class="ghost-button" data-list-toggle>List</button>'}
        </div>
        <div class="list-row" hidden>
          <input type="number" min="1" max="1000000" step="1" placeholder="Price" aria-label="Listing price" />
          <button type="button" class="primary-button" data-list-confirm data-item-id="${item.id}">Confirm</button>
        </div>`}
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

interface SummaryPlaque {
  kind: "coin" | "item" | "turns" | "foe" | "none";
  label: string;
  value: string;
  count?: number;
}

function escapeHtml(value: string): string {
  return value.replace(/[&<>"']/g, (char) => (
    { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[char] as string
  ));
}

function animateCount(element: HTMLElement, target: number): void {
  if (target <= 0 || window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    element.textContent = `+${target}`;
    return;
  }
  const start = performance.now();
  const duration = 700;
  const tick = (now: number): void => {
    const progress = Math.min(1, (now - start) / duration);
    element.textContent = `+${Math.round(target * (1 - (1 - progress) ** 3))}`;
    if (progress < 1) window.requestAnimationFrame(tick);
  };
  window.requestAnimationFrame(tick);
}

function clearOutcomePose(root: HTMLElement): void {
  root.querySelectorAll(".cat-avatar, .enemy-body").forEach((element) => {
    element.classList.remove("is-winner", "is-defeated");
  });
}

function applyOutcomePose(root: HTMLElement, result: "player" | "enemy"): void {
  clearOutcomePose(root);
  const player = root.querySelector<HTMLElement>(".fighter-player .cat-avatar");
  const enemy = root.querySelector<HTMLElement>(".fighter-enemy .enemy-body");
  const [winner, loser] = result === "player" ? [player, enemy] : [enemy, player];
  [winner, loser].forEach((element) => element?.classList.remove("attack-lunge"));
  winner?.classList.add("is-winner");
  loser?.classList.add("is-defeated");
}

function resetBattleSummary(root: HTMLElement): void {
  clearOutcomePose(root);
  const card = root.querySelector<HTMLElement>("#battle-summary");
  if (!card) return;
  card.dataset.state = "idle";
  card.innerHTML = '<p class="result-idle">Battle results will appear here.</p>';
}

function renderPlaque(plaque: SummaryPlaque, index: number): string {
  const icon = plaque.kind === "coin" ? '<span class="plaque-icon coin-icon" aria-hidden="true"></span>'
    : plaque.kind === "item" ? '<span class="plaque-icon gem-icon" aria-hidden="true"></span>'
    : plaque.kind === "turns" ? '<span class="plaque-icon turn-icon" aria-hidden="true">⏱</span>'
    : plaque.kind === "foe" ? '<span class="plaque-icon turn-icon" aria-hidden="true">⚔</span>'
    : '<span class="plaque-icon turn-icon" aria-hidden="true">–</span>';
  const count = plaque.count !== undefined ? ` data-count="${plaque.count}"` : "";
  return `
    <div class="plaque plaque-${plaque.kind}" style="--i:${index}">
      ${icon}
      <span class="plaque-text">
        <span class="plaque-label">${escapeHtml(plaque.label)}</span>
        <strong${count}>${escapeHtml(plaque.value)}</strong>
      </span>
    </div>`;
}

function showBattleSummary(
  root: HTMLElement,
  summary: { won: boolean; subtitle: string; plaques: SummaryPlaque[] },
): void {
  const card = root.querySelector<HTMLElement>("#battle-summary");
  if (!card) return;
  card.dataset.state = summary.won ? "win" : "loss";
  card.innerHTML = `
    <div class="result-banner">
      <span class="result-title">${summary.won ? "VICTORY" : "DEFEAT"}</span>
      <span class="result-subtitle">${escapeHtml(summary.subtitle)}</span>
    </div>
    <div class="result-plaques">${summary.plaques.map(renderPlaque).join("")}</div>`;
  card.querySelectorAll<HTMLElement>("[data-count]").forEach((element) => {
    animateCount(element, Number(element.dataset.count));
  });
  applyOutcomePose(root, summary.won ? "player" : "enemy");
}

function showPveSummary(root: HTMLElement, battle: BattleRead): void {
  const won = battle.result === "player";
  const enemy = battle.enemy_snapshot.name;
  const plaques: SummaryPlaque[] = [];
  if (battle.reward) {
    plaques.push({
      kind: "coin",
      label: "Coins won",
      value: `+${battle.reward.currency_amount}`,
      count: battle.reward.currency_amount,
    });
    if (battle.reward.item_instance_id) {
      plaques.push({ kind: "item", label: "New item", value: "In backpack" });
    }
  } else {
    plaques.push({ kind: "none", label: "Reward", value: "None" });
  }
  plaques.push({
    kind: "turns",
    label: "Turns",
    value: String(Math.max(0, ...battle.events.map((event) => event.turn_number))),
  });
  showBattleSummary(root, {
    won,
    subtitle: won ? `${enemy} was defeated.` : `${enemy} was too tough. Gear up and try again.`,
    plaques,
  });
}

function showPvpSummary(root: HTMLElement, match: PvpMatchRead, opponent: string): void {
  const won = match.result === "challenger";
  showBattleSummary(root, {
    won,
    subtitle: won ? `Your cat beat ${opponent}'s build.` : `${opponent}'s build won this round.`,
    plaques: [
      { kind: "foe", label: "Opponent", value: opponent },
      { kind: "turns", label: "Turns", value: String(match.turn_count) },
    ],
  });
}

function bumpCoins(root: HTMLElement): void {
  const badge = root.querySelector<HTMLElement>("#coins-badge");
  if (!badge) return;
  badge.classList.remove("is-bumped");
  void badge.offsetWidth;
  badge.classList.add("is-bumped");
}

function setFightButtonState(root: HTMLElement, pending: boolean): void {
  const fightButton = root.querySelector<HTMLButtonElement>('[data-action="fight"]');
  const skipButton = root.querySelector<HTMLButtonElement>('[data-action="skip-battle"]');
  if (!fightButton || !skipButton) return;

  fightButton.disabled = pending;
  fightButton.textContent = pending ? "Fighting…" : "Fight";
  fightButton.hidden = pending;
  skipButton.hidden = !pending;
}
