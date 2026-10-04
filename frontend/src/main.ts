import "./styles.css";
import { mountDashboard } from "./screens/dashboard";
import { getCurrentPlayer } from "./api/authApi";
import { mountAuth } from "./screens/auth";

const appRoot = document.querySelector<HTMLDivElement>("#app");

if (appRoot) {
  void getCurrentPlayer()
    .then(() => mountDashboard(appRoot))
    .catch(() => {
      mountAuth(appRoot, () => mountDashboard(appRoot));
      appRoot.addEventListener("authenticated", () => mountDashboard(appRoot), { once: true });
    });
}
