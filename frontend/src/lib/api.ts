// Thin fetch wrapper around the FastAPI backend.

// Empty string = same origin. That is the deployed setup, where FastAPI serves
// both this app and /api. In local dev, .env.local sets NEXT_PUBLIC_API_URL to
// http://localhost:8000 because the two run as separate servers.
const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "";
const TOKEN_KEY = "inventory_token";

/** Read the stored bearer token (client-side only). */
export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

/** Persist the bearer token. */
export function setToken(token: string): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(TOKEN_KEY, token);
}

/** Remove the stored bearer token. */
export function clearToken(): void {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(TOKEN_KEY);
}

/** Error carrying the HTTP status so callers can branch on it. */
export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

interface RequestOptions {
  method?: string;
  body?: unknown;
  auth?: boolean;
}

/** Perform a JSON request against the backend API. */
export async function apiFetch<T>(
  path: string,
  { method = "GET", body, auth = false }: RequestOptions = {},
): Promise<T> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };

  if (auth) {
    const token = getToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_URL}${path}`, {
    method,
    headers,
    body: body === undefined ? undefined : JSON.stringify(body),
  });

  if (!res.ok) {
    let detail = `Request failed (${res.status})`;
    try {
      const data = await res.json();
      if (typeof data?.detail === "string") detail = data.detail;
    } catch {
      // Non-JSON error body; keep the default message.
    }
    throw new ApiError(detail, res.status);
  }

  // 204 No Content and similar have no body.
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}
