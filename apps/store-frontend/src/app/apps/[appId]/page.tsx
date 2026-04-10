/**
 * App Detail page — 70/30 layout per doc § 4.2.2.
 * Left: description, changelog, reviews.
 * Right: icon, download button, metadata.
 */

import { fetchApp, getDownloadUrl } from "@/lib/api";
import { SystemBadge } from "@/components/SystemBadge";
import { StatusBadge } from "@/components/StatusBadge";

interface PageProps {
  params: Promise<{ appId: string }>;
}

export default async function AppDetailPage({ params }: PageProps) {
  const { appId } = await params;

  let app;
  try {
    app = await fetchApp(appId);
  } catch {
    return (
      <div className="max-w-5xl mx-auto px-6 py-16 text-center">
        <div className="text-5xl mb-4">🔍</div>
        <h2 className="text-xl font-semibold text-gray-700 dark:text-gray-200">App không tồn tại</h2>
        <p className="text-gray-500 dark:text-gray-400 mt-2">
          Không tìm thấy app với ID: {appId}
        </p>
        <a href="/" className="inline-block mt-4 text-blue-600 dark:text-blue-400 hover:underline">
          ← Quay lại App Store
        </a>
      </div>
    );
  }

  const displayName = app.name.length > 80 ? app.name.slice(0, 77) + "..." : app.name;
  const initial = app.name.charAt(0).toUpperCase();

  return (
    <div className="max-w-5xl mx-auto px-6 py-6">
      {/* Breadcrumb */}
      <nav className="text-sm text-gray-500 dark:text-gray-400 mb-4">
        <a href="/" className="hover:text-blue-600 dark:hover:text-blue-400">App Store</a>
        <span className="mx-2">/</span>
        <span className="text-gray-900 dark:text-white">{displayName}</span>
      </nav>

      {/* 70/30 layout */}
      <div className="flex gap-8">
        {/* LEFT COLUMN (70%) */}
        <div className="flex-1 min-w-0">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white" title={app.name}>
            {displayName}
          </h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            v{app.version}
            {app.vendor_name && <> · {app.vendor_name}</>}
          </p>

          {/* Description */}
          <div className="mt-6 prose prose-sm max-w-none text-gray-700 dark:text-gray-300">
            <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-100">Mô tả</h2>
            <p className="whitespace-pre-wrap">{app.description || "Chưa có mô tả chi tiết."}</p>
          </div>

          {/* What's New */}
          <div className="mt-8">
            <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-100">Có gì mới</h2>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">
              Phiên bản {app.version} — phiên bản đầu tiên.
            </p>
          </div>

          {/* Reviews */}
          <div className="mt-8">
            <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-100">Đánh giá</h2>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">Chưa có đánh giá nào.</p>
          </div>
        </div>

        {/* RIGHT COLUMN (30%) */}
        <aside className="w-72 flex-shrink-0">
          <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-5 sticky top-6">
            {/* Large icon */}
            <div className="flex justify-center mb-4">
              <div
                className="bg-gray-200 dark:bg-gray-700 rounded-xl flex items-center justify-center text-gray-500 dark:text-gray-300 font-bold"
                style={{ width: 128, height: 128, fontSize: 48 }}
              >
                {initial}
              </div>
            </div>

            {/* Download button */}
            {app.status === "approved" ? (
              <a
                href={getDownloadUrl(app.app_id)}
                download
                className="block w-full text-center bg-blue-600 text-white py-2.5 rounded-lg font-medium hover:bg-blue-700 transition-colors"
              >
                Tải xuống ZIP
              </a>
            ) : (
              <div className="text-center text-sm text-gray-500 dark:text-gray-400 py-2.5">
                App chưa được phê duyệt
              </div>
            )}

            {/* Metadata */}
            <div className="mt-5 space-y-3 text-sm">
              <div>
                <span className="text-gray-500 dark:text-gray-400">Tương thích:</span>
                <div className="mt-1 flex flex-wrap gap-1">
                  {app.systems?.map((s) => <SystemBadge key={s} system={s} />) || (
                    <span className="text-gray-400">—</span>
                  )}
                </div>
              </div>

              <div>
                <span className="text-gray-500 dark:text-gray-400">Modules:</span>
                <p className="text-gray-800 dark:text-gray-200">
                  {app.modules?.join(", ") || "—"}
                </p>
              </div>

              <div>
                <span className="text-gray-500 dark:text-gray-400">Phiên bản tối thiểu:</span>
                <p className="text-gray-800 dark:text-gray-200">{app.min_version || "—"}</p>
              </div>

              <div>
                <span className="text-gray-500 dark:text-gray-400">Trạng thái:</span>
                <div className="mt-1">
                  <StatusBadge status={app.status} />
                </div>
              </div>

              <div>
                <span className="text-gray-500 dark:text-gray-400">Lượt tải:</span>
                <p className="text-gray-800 dark:text-gray-200">{app.download_count.toLocaleString()}</p>
              </div>

              {app.rating_avg && (
                <div>
                  <span className="text-gray-500 dark:text-gray-400">Đánh giá:</span>
                  <p className="text-yellow-600 dark:text-yellow-400">
                    {"★".repeat(Math.round(app.rating_avg))} {app.rating_avg.toFixed(1)}/5
                  </p>
                </div>
              )}

              {app.published_at && (
                <div>
                  <span className="text-gray-500 dark:text-gray-400">Ngày phát hành:</span>
                  <p className="text-gray-800 dark:text-gray-200">
                    {new Date(app.published_at).toLocaleDateString("vi-VN")}
                  </p>
                </div>
              )}
            </div>
          </div>
        </aside>
      </div>
    </div>
  );
}
