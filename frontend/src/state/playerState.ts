import type { ItemInstanceRead, SlotKey, StatKey } from "../types";

export const SLOT_ORDER: SlotKey[] = ["head", "body", "weapon", "accessory"];

export function sumBonusForStat(items: ItemInstanceRead[], statKey: StatKey): number {
  return items.reduce((total, item) => total + (item.definition.modifiers[statKey] ?? 0), 0);
}

export function getEquippedItemsForCat(
  inventory: ItemInstanceRead[],
  catId: string,
): ItemInstanceRead[] {
  return inventory.filter((item) => item.equipped_cat_id === catId);
}
