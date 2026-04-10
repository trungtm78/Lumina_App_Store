/**
 * API client for App Engine (running inside Lumina Core).
 * In v1, we proxy through the store-backend or call Core directly.
 * For now, this uses local state to simulate the engine behavior.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface InstalledApp {
  app_id: string;
  name: string;
  version: string;
  description_short: string;
  systems: string[];
  modules: string[];
  is_active: boolean;
}

export interface InstallProgress {
  step: string;
  percent: number;
}

// Simulate installed apps (in production, App Engine provides this via API)
let _installedApps: InstalledApp[] = [];

export function getInstalledApps(): InstalledApp[] {
  return [..._installedApps];
}

export function activateApp(appId: string): { success: boolean; message: string } {
  const app = _installedApps.find((a) => a.app_id === appId);
  if (!app) return { success: false, message: "App not found" };
  if (app.is_active) return { success: true, message: "already active" };
  app.is_active = true;
  return { success: true, message: "activated" };
}

export function deactivateApp(appId: string): { success: boolean; message: string } {
  const app = _installedApps.find((a) => a.app_id === appId);
  if (!app) return { success: false, message: "App not found" };
  if (!app.is_active) return { success: true, message: "already inactive" };
  app.is_active = false;
  return { success: true, message: "deactivated" };
}

export async function installFromStore(
  appId: string,
  onProgress?: (p: InstallProgress) => void
): Promise<{ success: boolean; message: string }> {
  // Simulate the 1-click install flow from the plan
  const steps = [
    { step: "Downloading...", percent: 20 },
    { step: "Verifying checksum...", percent: 40 },
    { step: "Extracting...", percent: 60 },
    { step: "Registering...", percent: 80 },
    { step: "Complete!", percent: 100 },
  ];

  for (const s of steps) {
    onProgress?.(s);
    await new Promise((r) => setTimeout(r, 400));
  }

  // Fetch app info from store
  try {
    const res = await fetch(`${API_BASE}/api/apps/${appId}`);
    if (!res.ok) throw new Error("App not found in store");
    const app = await res.json();

    // Check if already installed
    if (_installedApps.some((a) => a.app_id === appId)) {
      // Upgrade: update version
      const existing = _installedApps.find((a) => a.app_id === appId)!;
      existing.version = app.version;
      return { success: true, message: `Upgraded to v${app.version}` };
    }

    _installedApps.push({
      app_id: app.app_id,
      name: app.name,
      version: app.version,
      description_short: app.description_short || "",
      systems: app.systems || [],
      modules: app.modules || [],
      is_active: false,
    });

    return { success: true, message: "Installed" };
  } catch (e: any) {
    return { success: false, message: e.message };
  }
}
