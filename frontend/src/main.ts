import "./styles.css";

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

document.querySelector<HTMLDivElement>("#app")!.innerHTML = `
  <main class="shell">
    <header class="topbar">
      <div>
        <p class="eyebrow">PIXEL CAT ARENA</p>
        <h1>Build. Battle. Trade.</h1>
      </div>
      <span class="status" id="api-status">Checking API…</span>
    </header>
    <section class="hero">
      <div class="cat-stage" aria-label="Pixel cat preview">
        <div class="cat">ฅ^•ﻌ•^ฅ</div>
      </div>
      <div class="panel">
        <p class="eyebrow">STARTER CAT</p>
        <h2>Your arena awaits</h2>
        <p>Equip your cat, fight automatic battles, and earn gear to trade.</p>
        <div class="stats">
          <span>ATK <strong>10</strong></span>
          <span>DEF <strong>10</strong></span>
          <span>SPD <strong>10</strong></span>
        </div>
        <button type="button" disabled>Fight a battle</button>
      </div>
    </section>
  </main>
`;

async function checkApi(): Promise<void> {
  const status = document.querySelector<HTMLSpanElement>("#api-status");
  if (!status) return;

  try {
    const response = await fetch(`${apiBaseUrl}/health`);
    status.textContent = response.ok ? "API online" : "API needs setup";
    status.dataset.connected = String(response.ok);
  } catch {
    status.textContent = "API offline";
    status.dataset.connected = "false";
  }
}

void checkApi();
