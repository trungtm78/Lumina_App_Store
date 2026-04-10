/**
 * API client for Live Skill Authoring endpoints.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface FileEntry {
  path: string;
  size: number;
  modified: string;
}

export interface SaveResult {
  app_id: string;
  path: string;
  saved: boolean;
  validation_errors: string[];
}

export interface DeployResult {
  app_id: string;
  version: string;
  deployed_at: string;
  snapshot_path: string;
}

export interface VersionEntry {
  timestamp: string;
  version: string;
  path: string;
}

export async function createApp(appId: string, name: string) {
  const res = await fetch(`${API_BASE}/api/authoring/new`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ app_id: appId, name }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Error ${res.status}`);
  }
  return res.json();
}

export async function listFiles(appId: string): Promise<FileEntry[]> {
  const res = await fetch(`${API_BASE}/api/authoring/${appId}/files`);
  if (!res.ok) throw new Error(`Error ${res.status}`);
  const data = await res.json();
  return data.files;
}

export async function readFile(appId: string, path: string): Promise<string> {
  const res = await fetch(`${API_BASE}/api/authoring/${appId}/files/${path}`);
  if (!res.ok) throw new Error(`Error ${res.status}`);
  const data = await res.json();
  return data.content;
}

export async function saveFile(appId: string, path: string, content: string): Promise<SaveResult> {
  const res = await fetch(`${API_BASE}/api/authoring/${appId}/files/${path}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content }),
  });
  if (!res.ok) throw new Error(`Error ${res.status}`);
  return res.json();
}

export async function deployApp(appId: string): Promise<DeployResult> {
  const res = await fetch(`${API_BASE}/api/authoring/${appId}/deploy`, { method: "POST" });
  if (!res.ok) throw new Error(`Error ${res.status}`);
  return res.json();
}

export async function listVersions(appId: string): Promise<VersionEntry[]> {
  const res = await fetch(`${API_BASE}/api/authoring/${appId}/versions`);
  if (!res.ok) throw new Error(`Error ${res.status}`);
  const data = await res.json();
  return data.versions;
}

export async function rollback(appId: string, timestamp: string) {
  const res = await fetch(`${API_BASE}/api/authoring/${appId}/rollback/${timestamp}`, {
    method: "POST",
  });
  if (!res.ok) throw new Error(`Error ${res.status}`);
  return res.json();
}

export function getWsUrl(appId: string): string {
  const wsBase = API_BASE.replace(/^http/, "ws");
  return `${wsBase}/api/authoring/ws/${appId}`;
}
