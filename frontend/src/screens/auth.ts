import { login, register } from "../api/authApi";

export function mountAuth(root: HTMLElement, onAuthenticated: () => void): void {
  root.innerHTML = `
    <main class="auth-shell">
      <section class="panel auth-panel">
        <div class="auth-mascot" aria-hidden="true">🐱</div>
        <p class="eyebrow">PIXEL CAT ARENA</p>
        <h1>Enter the arena</h1>
        <p class="auth-copy">Create a local account or sign in to your cat.</p>
        <form id="auth-form">
          <label>Username<input name="username" minlength="3" maxlength="50" required autocomplete="username" placeholder="e.g. mochi_tamer"></label>
          <label>Password<input name="password" type="password" minlength="8" maxlength="128" required autocomplete="current-password" placeholder="At least 8 characters"></label>
          <p id="auth-error" class="error-message" aria-live="polite"></p>
          <div class="auth-actions">
            <button class="primary-button" type="submit" data-auth-mode="login">Log in</button>
            <button class="ghost-button" type="button" data-auth-mode="register">Create account</button>
          </div>
        </form>
      </section>
    </main>
  `;

  root.querySelector<HTMLFormElement>("#auth-form")?.addEventListener("submit", async (event) => {
    event.preventDefault();
    await submitAuth(root, "login", onAuthenticated);
  });
  root.querySelector<HTMLButtonElement>('[data-auth-mode="register"]')?.addEventListener("click", () => {
    void submitAuth(root, "register", onAuthenticated);
  });
}

async function submitAuth(
  root: HTMLElement,
  mode: "login" | "register",
  onAuthenticated: () => void,
): Promise<void> {
  const form = root.querySelector<HTMLFormElement>("#auth-form");
  const error = root.querySelector<HTMLElement>("#auth-error");
  if (!form) return;
  const data = new FormData(form);
  try {
    const username = String(data.get("username") ?? "");
    const password = String(data.get("password") ?? "");
    if (mode === "register") await register(username, password);
    else await login(username, password);
    onAuthenticated();
  } catch (reason) {
    if (error) error.textContent = reason instanceof Error ? reason.message : "Authentication failed.";
  }
}
