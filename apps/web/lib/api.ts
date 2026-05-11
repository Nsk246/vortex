import type { CaseDetail, CaseSummary } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
const WS_BASE = process.env.NEXT_PUBLIC_WS_BASE_URL ?? "ws://localhost:8000";

export function getToken() {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem("vortex_token");
}

export function setToken(token: string) {
  window.localStorage.setItem("vortex_token", token);
}

type RequestOptions = RequestInit & {
  timeoutMs?: number;
  requireAuth?: boolean;
};

function formatApiError(error: unknown, fallback: string) {
  if (!error || typeof error !== "object") return fallback;
  const detail = "detail" in error ? (error as { detail?: unknown }).detail : undefined;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (!item || typeof item !== "object") return String(item);
        const issue = item as { loc?: unknown[]; msg?: string };
        const field = Array.isArray(issue.loc) ? issue.loc[issue.loc.length - 1] : null;
        return field ? `${String(field)}: ${issue.msg ?? "Invalid value"}` : issue.msg ?? "Invalid value";
      })
      .join(". ");
  }
  return fallback;
}

async function request<T>(path: string, init: RequestOptions = {}): Promise<T> {
  const token = getToken();
  if (init.requireAuth !== false && !token) {
    throw new Error("Sign in or create a workspace before uploading evidence.");
  }
  const { timeoutMs = 20000, requireAuth: _requireAuth, ...requestInit } = init;
  const headers = new Headers(init.headers);
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (!(init.body instanceof FormData)) headers.set("Content-Type", "application/json");
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), timeoutMs);
  let response: Response;
  try {
    response = await fetch(`${API_BASE}${path}`, { ...requestInit, headers, signal: controller.signal });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new Error("The request is taking too long. Check Docker/API logs and try again.");
    }
    throw new Error("Could not reach the VORTEX API. Confirm the API is running on port 8000.");
  } finally {
    window.clearTimeout(timeout);
  }
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(formatApiError(error, response.statusText || "Request failed"));
  }
  return response.json() as Promise<T>;
}

export async function login(email: string, password: string) {
  const data = await request<{ access_token: string }>("/api/v1/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
    requireAuth: false,
  });
  setToken(data.access_token);
}

export async function register(email: string, password: string, fullName: string, organizationName: string) {
  const data = await request<{ access_token: string }>("/api/v1/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, password, full_name: fullName, organization_name: organizationName }),
    requireAuth: false,
  });
  setToken(data.access_token);
}

export const listCases = () => request<CaseSummary[]>("/api/v1/cases");
export const getCase = (id: string) => request<CaseDetail>(`/api/v1/cases/${id}`);
export const createCase = (title: string) => request<CaseSummary>("/api/v1/cases", { method: "POST", body: JSON.stringify({ title }) });
export const runCase = (id: string) => request<{ task_id: string }>(`/api/v1/cases/${id}/run`, { method: "POST" });

export async function uploadMedia(caseId: string, file: File) {
  const body = new FormData();
  body.append("file", file);
  return request(`/api/v1/cases/${caseId}/media`, { method: "POST", body, timeoutMs: 10 * 60 * 1000 });
}

export function caseStreamUrl(caseId: string) {
  return `${WS_BASE}/api/v1/cases/${caseId}/stream`;
}
