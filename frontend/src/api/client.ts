export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const requestHeaders = new Headers(options.headers ?? {});

  if (!requestHeaders.has("Content-Type") && options.method && options.method.toUpperCase() !== "GET") {
    requestHeaders.set("Content-Type", "application/json");
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    credentials: "include",
    headers: requestHeaders,
  });

  if (!response.ok) {
    let errorMessage = `Request failed (${response.status})`;

    try {
      const body = await response.json();
      if (typeof body?.detail === "string") {
        errorMessage = body.detail;
      } else if (body && typeof body === "object") {
        errorMessage = JSON.stringify(body);
      }
    } catch {
      // Ignore JSON parsing errors and preserve the fallback message.
    }

    throw new Error(errorMessage);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}
