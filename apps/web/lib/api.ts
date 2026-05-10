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

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers = new Headers(init.headers);
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (!(init.body instanceof FormData)) headers.set("Content-Type", "application/json");
  const response = await fetch(`${API_BASE}${path}`, { ...init, headers });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail ?? "Request failed");
  }
  return response.json() as Promise<T>;
}

export async function login(email: string, password: string) {
  const data = await request<{ access_token: string }>("/api/v1/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password })
  });
  setToken(data.access_token);
}

export async function register(email: string, password: string, fullName: string, organizationName: string) {
  const data = await request<{ access_token: string }>("/api/v1/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, password, full_name: fullName, organization_name: organizationName })
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
  return request(`/api/v1/cases/${caseId}/media`, { method: "POST", body });
}

export function caseStreamUrl(caseId: string) {
  return `${WS_BASE}/api/v1/cases/${caseId}/stream`;
}

