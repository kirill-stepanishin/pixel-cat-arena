import "./styles.css";
import { mountDashboard } from "./screens/dashboard";

const appRoot = document.querySelector<HTMLDivElement>("#app");

if (appRoot) {
  mountDashboard(appRoot);
}
