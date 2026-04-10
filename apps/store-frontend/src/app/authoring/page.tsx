/**
 * Authoring index — create new app or pick existing draft.
 */

"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { createApp } from "@/lib/authoring-api";

export default function AuthoringIndexPage() {
  const router = useRouter();
  const [appId, setAppId] = useState("");
  const [appName, setAppName] = useState("");
  const [error, setError] = useState("");
  const [creating, setCreating] = useState(false);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!appId.trim() || !appName.trim()) return;

    setCreating(true);
    setError("");
    try {
      await createApp(appId.trim(), appName.trim());
      router.push(`/authoring/${appId.trim()}`);
    } catch (e: any) {
      setError(e.message);
    }
    setCreating(false);
  }

  return (
    <div className="max-w-xl mx-auto px-6 py-16">
      <h1 className="text-2xl font-bold text-gray-900 mb-2">Live Skill Authoring</h1>
      <p className="text-gray-500 mb-8">
        Tạo app mới hoặc mở app có sẵn để chỉnh sửa. Viết skill.md, test AI ngay trong browser.
      </p>

      {/* Create new */}
      <div className="bg-white border border-gray-200 rounded-xl p-6">
        <h2 className="text-lg font-semibold text-gray-800 mb-4">Tạo app mới</h2>
        <form onSubmit={handleCreate} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              App ID (slug)
            </label>
            <input
              type="text"
              value={appId}
              onChange={(e) => setAppId(e.target.value.toLowerCase().replace(/[^a-z0-9-]/g, "-"))}
              placeholder="my-awesome-app"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              pattern="^[a-z0-9][a-z0-9-]*[a-z0-9]$"
              minLength={3}
              required
            />
            <p className="text-xs text-gray-400 mt-1">Chỉ chữ thường, số, dấu gạch ngang</p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Tên hiển thị
            </label>
            <input
              type="text"
              value={appName}
              onChange={(e) => setAppName(e.target.value)}
              placeholder="My Awesome App"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>

          {error && (
            <div className="text-sm text-red-600 bg-red-50 px-3 py-2 rounded">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={creating || !appId.trim() || !appName.trim()}
            className="w-full py-2.5 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {creating ? "Đang tạo..." : "Tạo và mở editor"}
          </button>
        </form>
      </div>

      {/* Open existing */}
      <div className="mt-6 bg-white border border-gray-200 rounded-xl p-6">
        <h2 className="text-lg font-semibold text-gray-800 mb-4">Mở app có sẵn</h2>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            const input = (e.target as HTMLFormElement).elements.namedItem("existingId") as HTMLInputElement;
            if (input.value.trim()) {
              router.push(`/authoring/${input.value.trim()}`);
            }
          }}
          className="flex gap-2"
        >
          <input
            name="existingId"
            type="text"
            placeholder="app-id"
            className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            type="submit"
            className="px-4 py-2 bg-gray-100 text-gray-700 text-sm font-medium rounded-lg hover:bg-gray-200"
          >
            Mở
          </button>
        </form>
      </div>
    </div>
  );
}
