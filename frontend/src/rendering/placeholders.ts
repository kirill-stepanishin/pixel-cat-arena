export function renderCat(
  enemy = false,
  equippedItems: Array<{ visualKey: string; slot: string }> = [],
): string {
  const asset = enemy ? "enemy-cat" : "mochi";
  const equipmentLayers = layersForSlots(equippedItems, ["body", "accessory", "head", "weapon"]);
  return `
    <span class="cat-composition">
      <img src="/assets/cats/${asset}.png" alt="" class="cat-sprite" />
      ${equipmentLayers}
    </span>
  `;
}

function layersForSlots(
  equippedItems: Array<{ visualKey: string; slot: string }>,
  slots: string[],
): string {
  return slots
    .flatMap((slot) => equippedItems.filter((item) => item.slot === slot))
    .map(({ visualKey, slot }) =>
      `<img src="/assets/items/${slot}/${visualKey}.png" alt="" class="cat-equipment-layer" />`
    )
    .join("");
}
