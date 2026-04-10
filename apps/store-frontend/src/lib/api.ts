/**
 * API client for Lumina App Store backend.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface AppItem {
  id: string;
  app_id: string;
  name: string;
  version: string;
  description: string | null;
  description_short: string | null;
  category: string | null;
  systems: string[] | null;
  modules: string[] | null;
  min_version: string | null;
  status: string;
  download_count: number;
  rating_avg: number | null;
  is_featured: boolean;
  published_at: string | null;
  vendor_name: string | null;
  created_at: string;
  updated_at: string;
}

export interface AppListResponse {
  items: AppItem[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface AppListParams {
  page?: number;
  page_size?: number;
  system?: string;
  category?: string;
  status?: string;
  search?: string;
  sort?: string;
}

export async function fetchApps(params: AppListParams = {}): Promise<AppListResponse> {
  const searchParams = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      searchParams.set(key, String(value));
    }
  });

  const url = `${API_BASE}/api/apps?${searchParams.toString()}`;
  const res = await fetch(url, { cache: "no-store" });

  if (!res.ok) {
    throw new Error(`API error: ${res.status}`);
  }

  return res.json();
}

export async function fetchApp(appId: string): Promise<AppItem> {
  const res = await fetch(`${API_BASE}/api/apps/${appId}`, { cache: "no-store" });

  if (!res.ok) {
    if (res.status === 404) throw new Error("App not found");
    throw new Error(`API error: ${res.status}`);
  }

  return res.json();
}

export function getDownloadUrl(appId: string): string {
  return `${API_BASE}/api/apps/${appId}/download`;
}
