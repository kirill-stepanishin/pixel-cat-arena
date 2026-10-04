export function renderGlyph(visualKey: string, slot?: string): string {
  const fallback = "items/unknown.png";
  const assetKey = visualKey && slot ? `${slot}/${visualKey}` : fallback;
  return `<img src="/assets/items/${assetKey}.png" alt="" class="sprite-image" />`;
}

export function renderCat(
  enemy = false,
  equippedItems: Array<{ visualKey: string; slot: string }> = [],
): string {
  const asset = enemy ? "enemy-cat" : "mochi";
  const headLayers = layersForSlots(equippedItems, ["head"]);
  const foregroundLayers = layersForSlots(equippedItems, ["body", "accessory", "weapon"]);
  return `
    <span class="cat-composition">
      <img src="/assets/cats/${asset}.png" alt="" class="cat-sprite" />
      ${headLayers}
      ${foregroundLayers}
    </span>
  `;
}

function layersForSlots(
  equippedItems: Array<{ visualKey: string; slot: string }>,
  slots: string[],
): string {
  return equippedItems
    .filter(({ slot }) => slots.includes(slot))
    .map(({ visualKey, slot }) =>
      `<img src="/assets/items/${slot}/${visualKey}.png" alt="" class="cat-equipment-layer" />`
    )
    .join("");
}
