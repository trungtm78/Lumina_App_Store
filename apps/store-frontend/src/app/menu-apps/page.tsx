/**
 * Menu Apps page — simulates the in-Core apps management UI.
 * Shows installed apps with activate/deactivate toggles.
 * "Browse Store" opens a panel with 1-click install flow.
 *
 * Per doc § 5.4: sidebar menu item, main content shows installed apps.
 */

"use client";

import { useCallback, useEffect, useState } from "react";
import { SystemBadge } from "@/components/SystemBadge";
import {
  getInstalledApps,
  activateApp,
  deactivateApp,
  installFromStore,
  type InstalledApp,
  type InstallProgress,
} from "@/lib/engine-api";
import { fetchApps, type AppItem } from "@/lib/api";

type View = "installed" | "store";

export default function MenuAppsPage() {
  const [view, setView] = useState<View>("installed");
  const [installedApps, setInstalledApps] = useState<InstalledApp[]>([]);
  const [storeApps, setStoreApps] = useState<AppItem[]>([]);
  const [installing, setInstalling] = useState<string | null>(null);
  const [installProgress, setInstallProgress] = useState<InstallProgress | null>(null);
  const [confirmInstall, setConfirmInstall] = useState<AppItem | null>(null);
  const [toast, setToast] = useState<{ message: string; type: "success" | "error" } | null>(null);

  useEffect(() => {
    setInstalledApps(getInstalledApps());
  }, []);

  useEffect(() => {
    if (view === "store") {
      fetchApps({ status: "approved", page_size: 50 })
        .then((data) => setStoreApps(data.items))
        .catch(() => setStoreApps([]));
    }
  }, [view]);

  function showToast(message: string, type: "success" | "error" = "success") {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3000);
  }

  function handleToggle(appId: string, currentlyActive: boolean) {
    const result = currentlyActive ? deactivateApp(appId) : activateApp(appId);
    if (result.success) {
      setInstalledApps(getInstalledApps());
      showToast(currentlyActive ? `${appId} deactivated` : `${appId} activated`);
    } else {
      showToast(result.message, "error");
    }
  }

  async function handleInstall(app: AppItem) {
    setConfirmInstall(null);
    setInstalling(app.app_id);
    setInstallProgress(null);

    const result = await installFromStore(app.app_id, (p) => setInstallProgress(p));
    setInstalling(null);
    setInstallProgress(null);

    if (result.success) {
      setInstalledApps(getInstalledApps());
      showToast(`${app.name} installed!`);
    } else {
      showToast(`Install failed: ${result.message}`, "error");
    }
  }

  const isInstalled = useCallback(
    (appId: string) => installedApps.some((a) => a.app_id === appId),
    [installedApps]
  );

  return (
    <div className="max-w-4xl mx-auto px-6 py-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Apps</h1>
        <button
          onClick={() => setView(view === "installed" ? "store" : "installed")}
          className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700"
        >
          {view === "installed" ? "+ Browse Store" : "← Installed Apps"}
        </button>
      </div>

      {/* Toast */}
      {toast && (
        <div
          className={`fixed top-4 right-4 px-4 py-3 rounded-lg shadow-lg text-sm font-medium z-50 ${
            toast.type === "success"
              ? "bg-green-600 text-white"
              : "bg-red-600 text-white"
          }`}
        >
          {toast.message}
        </div>
      )}

      {/* Confirm dialog */}
      {confirmInstall && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-40">
          <div className="bg-white dark:bg-gray-800 rounded-xl p-6 max-w-sm shadow-xl">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Install {confirmInstall.name}?
            </h3>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">
              Install {confirmInstall.name} v{confirmInstall.version}? This will add it to your Apps folder.
            </p>
            <div className="flex gap-3 mt-4">
              <button
                onClick={() => handleInstall(confirmInstall)}
                className="flex-1 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700"
              >
                Install
              </button>
              <button
                onClick={() => setConfirmInstall(null)}
                className="flex-1 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-200 text-sm font-medium rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Install progress */}
      {installing && installProgress && (
        <div className="mb-4 bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center justify-between text-sm text-blue-700 mb-2">
            <span>{installProgress.step}</span>
            <span>{installProgress.percent}%</span>
          </div>
          <div className="w-full bg-blue-200 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${installProgress.percent}%` }}
            />
          </div>
        </div>
      )}

      {/* INSTALLED VIEW */}
      {view === "installed" && (
        <div className="space-y-3">
          {installedApps.length === 0 ? (
            <div className="text-center py-16">
              <div className="text-5xl mb-4">📦</div>
              <h3 className="text-lg font-medium text-gray-600 dark:text-gray-300">Chưa có app nào</h3>
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                Nhấn "Browse Store" để tìm và cài đặt app
              </p>
            </div>
          ) : (
            installedApps.map((app) => (
              <div
                key={app.app_id}
                className="flex items-center justify-between bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg px-5 py-4"
              >
                <div className="flex items-center gap-4">
                  <div
                    className={`w-3 h-3 rounded-full ${
                      app.is_active ? "bg-green-500" : "bg-gray-300"
                    }`}
                    aria-label={app.is_active ? "Active" : "Inactive"}
                  />
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-gray-900 dark:text-white">{app.name}</span>
                      <span className="text-xs text-gray-400 dark:text-gray-500">v{app.version}</span>
                    </div>
                    <p className="text-sm text-gray-500 dark:text-gray-400">{app.description_short}</p>
                    <div className="flex gap-1 mt-1">
                      {app.systems.map((s) => (
                        <SystemBadge key={s} system={s} />
                      ))}
                      <span className="text-xs text-gray-400 ml-2">
                        Module: {app.modules.join(", ")}
                      </span>
                    </div>
                  </div>
                </div>

                <button
                  onClick={() => handleToggle(app.app_id, app.is_active)}
                  className={`px-4 py-1.5 text-sm font-medium rounded-lg ${
                    app.is_active
                      ? "bg-gray-100 text-gray-700 hover:bg-gray-200"
                      : "bg-green-600 text-white hover:bg-green-700"
                  }`}
                >
                  {app.is_active ? "Deactivate" : "Activate"}
                </button>
              </div>
            ))
          )}
        </div>
      )}

      {/* STORE VIEW */}
      {view === "store" && (
        <div className="space-y-3">
          {storeApps.length === 0 ? (
            <div className="text-center py-16">
              <div className="text-5xl mb-4">🏪</div>
              <h3 className="text-lg font-medium text-gray-600 dark:text-gray-300">Store trống</h3>
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                Chưa có app nào được phê duyệt trên marketplace
              </p>
            </div>
          ) : (
            storeApps.map((app) => (
              <div
                key={app.app_id}
                className="flex items-center justify-between bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg px-5 py-4"
              >
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-gray-900 dark:text-white">{app.name}</span>
                    <span className="text-xs text-gray-400 dark:text-gray-500">v{app.version}</span>
                    {app.vendor_name && (
                      <span className="text-xs text-gray-400">by {app.vendor_name}</span>
                    )}
                  </div>
                  <p className="text-sm text-gray-500 mt-1">{app.description_short}</p>
                  <div className="flex gap-1 mt-1">
                    {app.systems?.map((s) => <SystemBadge key={s} system={s} />)}
                  </div>
                </div>

                {isInstalled(app.app_id) ? (
                  <span className="px-4 py-1.5 text-sm text-green-700 bg-green-50 rounded-lg font-medium">
                    Installed ✓
                  </span>
                ) : (
                  <button
                    onClick={() => setConfirmInstall(app)}
                    disabled={installing === app.app_id}
                    className="px-4 py-1.5 text-sm bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50"
                  >
                    Install
                  </button>
                )}
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}
