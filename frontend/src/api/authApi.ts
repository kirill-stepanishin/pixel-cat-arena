import { apiFetch } from "./client";
import type { PlayerWithDetails } from "../types";

export function getCurrentPlayer(): Promise<PlayerWithDetails> {
  return apiFetch<PlayerWithDetails>("/auth/me");
}

export function register(username: string, password: string): Promise<PlayerWithDetails> {
  return apiFetch<PlayerWithDetails>("/auth/register", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
}

export function login(username: string, password: string): Promise<PlayerWithDetails> {
  return apiFetch<PlayerWithDetails>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
}

export function logout(): Promise<void> {
  return apiFetch<void>("/auth/logout", { method: "POST" });
}
