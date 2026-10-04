export function renderGlyph(visualKey: string): string {
  const fallback = "items/unknown.png";
  const assetKey = visualKey || fallback;
  return `<img src="/assets/items/${assetKey}.png" alt="" class="sprite-image" />`;
}

export function renderCat(enemy = false, equippedVisualKeys: string[] = []): string {
  const asset = enemy ? "enemy-cat" : "mochi";
  const layers = equippedVisualKeys.map((visualKey) =>
    `<img src="/assets/items/${visualKey}.png" alt="" class="cat-equipment-layer" />`
  ).join("");
  return `
    <span class="cat-composition">
      <img src="/assets/cats/${asset}.png" alt="" class="cat-sprite" />
      ${layers}
    </span>
  `;
}
