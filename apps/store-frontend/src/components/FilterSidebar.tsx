/**
 * Filter sidebar — system, category, sort.
 */

"use client";

import { useRouter, useSearchParams } from "next/navigation";

const SYSTEMS = ["core", "plus", "storage", "care"];
const CATEGORIES = [
  "Chat",
  "Analytics",
  "Integration",
  "HR",
  "Finance",
  "Productivity",
  "Security",
  "DevTools",
  "Other",
];
const SORT_OPTIONS = [
  { value: "newest", label: "Mới nhất" },
  { value: "popular", label: "Phổ biến" },
  { value: "rating", label: "Đánh giá" },
  { value: "name", label: "Tên A-Z" },
];

export function FilterSidebar() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const currentSystem = searchParams.get("system") || "";
  const currentCategory = searchParams.get("category") || "";
  const currentSort = searchParams.get("sort") || "newest";

  function updateParam(key: string, value: string) {
    const params = new URLSearchParams(searchParams.toString());
    if (value) {
      params.set(key, value);
    } else {
      params.delete(key);
    }
    params.set("page", "1");
    router.push(`/?${params.toString()}`);
  }

  return (
    <aside className="w-56 flex-shrink-0 space-y-6">
      {/* System filter */}
      <div>
        <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">Hệ thống</h3>
        <div className="space-y-1">
          <button
            onClick={() => updateParam("system", "")}
            className={`block w-full text-left px-3 py-1.5 rounded text-sm ${
              !currentSystem
                ? "bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 font-medium"
                : "text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800"
            }`}
          >
            Tất cả
          </button>
          {SYSTEMS.map((s) => (
            <button
              key={s}
              onClick={() => updateParam("system", s)}
              className={`block w-full text-left px-3 py-1.5 rounded text-sm capitalize ${
                currentSystem === s
                  ? "bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 font-medium"
                  : "text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800"
              }`}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      {/* Category filter */}
      <div>
        <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">Danh mục</h3>
        <div className="space-y-1">
          <button
            onClick={() => updateParam("category", "")}
            className={`block w-full text-left px-3 py-1.5 rounded text-sm ${
              !currentCategory
                ? "bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 font-medium"
                : "text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800"
            }`}
          >
            Tất cả
          </button>
          {CATEGORIES.map((c) => (
            <button
              key={c}
              onClick={() => updateParam("category", c)}
              className={`block w-full text-left px-3 py-1.5 rounded text-sm ${
                currentCategory === c
                  ? "bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 font-medium"
                  : "text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800"
              }`}
            >
              {c}
            </button>
          ))}
        </div>
      </div>

      {/* Sort */}
      <div>
        <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">Sắp xếp</h3>
        <select
          value={currentSort}
          onChange={(e) => updateParam("sort", e.target.value)}
          className="w-full px-3 py-1.5 border border-gray-300 dark:border-gray-600 rounded text-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          aria-label="Sort apps"
        >
          {SORT_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </div>
    </aside>
  );
}
