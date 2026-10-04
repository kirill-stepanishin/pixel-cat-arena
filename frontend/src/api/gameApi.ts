import { apiFetch } from "./client";
import type {
  BattleRead,
  EnemyProgressRead,
  EnemyRead,
  ItemInstanceRead,
  PlayerWithDetails,
} from "../types";

const STORAGE_KEY = "pixel-cat-arena:player-id";

export function getStoredPlayerId(): string | null {
  return window.localStorage.getItem(STORAGE_KEY);
}

export function setStoredPlayerId(playerId: string): void {
  window.localStorage.setItem(STORAGE_KEY, playerId);
}

export async function ensureDevPlayer(): Promise<PlayerWithDetails> {
  const savedId = getStoredPlayerId();

  if (savedId) {
    try {
      return await getPlayer(savedId);
    } catch {
      window.localStorage.removeItem(STORAGE_KEY);
    }
  }

  const player = await apiFetch<PlayerWithDetails>("/dev/player", { method: "POST" });
  setStoredPlayerId(player.id);
  return player;
}

export async function getPlayer(playerId: string): Promise<PlayerWithDetails> {
  return apiFetch<PlayerWithDetails>(`/players/${playerId}`);
}

export async function getInventory(playerId: string): Promise<ItemInstanceRead[]> {
  return apiFetch<ItemInstanceRead[]>(`/players/${playerId}/items`);
}

export async function getCurrentEnemy(playerId: string): Promise<EnemyRead> {
  return apiFetch<EnemyRead>(`/battles/pve/current/${playerId}`);
}

export async function fightPve(playerId: string, enemyStage?: number): Promise<BattleRead> {
  return apiFetch<BattleRead>("/battles/pve", {
    method: "POST",
    body: JSON.stringify({ player_id: playerId, enemy_stage: enemyStage }),
  });
}

export async function getEnemyProgress(playerId: string): Promise<EnemyProgressRead> {
  return apiFetch<EnemyProgressRead>(`/battles/pve/enemies/${playerId}`);
}

export async function equipItem(playerId: string, catId: string, itemId: string): Promise<ItemInstanceRead> {
  return apiFetch<ItemInstanceRead>(`/players/${playerId}/cats/${catId}/items/${itemId}/equip`, {
    method: "POST",
  });
}

export async function unequipItem(
  playerId: string,
  catId: string,
  itemId: string,
): Promise<ItemInstanceRead> {
  return apiFetch<ItemInstanceRead>(`/players/${playerId}/cats/${catId}/items/${itemId}/unequip`, {
    method: "POST",
  });
}
