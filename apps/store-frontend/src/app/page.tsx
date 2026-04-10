/**
 * App List page — marketplace homepage.
 * Shows app grid with filter sidebar and search bar.
 */

import { Suspense } from "react";
import { fetchApps } from "@/lib/api";
import { AppCard } from "@/components/AppCard";
import { SearchBar } from "@/components/SearchBar";
import { FilterSidebar } from "@/components/FilterSidebar";

interface PageProps {
  searchParams: Promise<Record<string, string | undefined>>;
}

async function AppGrid({ searchParams }: { searchParams: Record<string, string | undefined> }) {
  try {
    const data = await fetchApps({
      page: Number(searchParams.page) || 1,
      page_size: 20,
      system: searchParams.system,
      category: searchParams.category,
      status: searchParams.status,
      search: searchParams.search,
      sort: searchParams.sort || "newest",
    });

    if (data.items.length === 0) {
      return (
        <div className="text-center py-16">
          <div className="text-gray-400 text-5xl mb-4">📦</div>
          <h3 className="text-lg font-medium text-gray-600 dark:text-gray-300">
            Không tìm thấy app nào
          </h3>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Thử thay đổi bộ lọc hoặc từ khóa tìm kiếm
          </p>
        </div>
      );
    }

    return (
      <div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {data.items.map((app) => (
            <AppCard key={app.app_id} app={app} />
          ))}
        </div>

        {/* Pagination */}
        {data.pages > 1 && (
          <div className="mt-6 flex justify-center gap-2">
            {Array.from({ length: data.pages }, (_, i) => i + 1).map((p) => (
              <a
                key={p}
                href={`/?${new URLSearchParams({
                  ...searchParams,
                  page: String(p),
                } as Record<string, string>).toString()}`}
                className={`px-3 py-1 rounded text-sm ${
                  p === data.page
                    ? "bg-blue-600 text-white"
                    : "bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
                }`}
              >
                {p}
              </a>
            ))}
          </div>
        )}

        <p className="mt-4 text-center text-xs text-gray-400 dark:text-gray-500">
          {data.total} apps
        </p>
      </div>
    );
  } catch {
    return (
      <div className="text-center py-16">
        <div className="text-red-400 text-5xl mb-4">⚠️</div>
        <h3 className="text-lg font-medium text-gray-600 dark:text-gray-300">
          Không thể kết nối đến server
        </h3>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          Kiểm tra backend đang chạy tại {process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}
        </p>
      </div>
    );
  }
}

export default async function HomePage({ searchParams }: PageProps) {
  const params = await searchParams;
  return (
    <div className="max-w-7xl mx-auto px-6 py-6">
      <div className="mb-6">
        <Suspense fallback={null}>
          <SearchBar />
        </Suspense>
      </div>

      <div className="flex gap-8">
        <Suspense fallback={null}>
          <FilterSidebar />
        </Suspense>
        <div className="flex-1">
          <AppGrid searchParams={params} />
        </div>
      </div>
    </div>
  );
}
