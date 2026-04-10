/**
 * App Card — grid item showing app summary.
 * Specs from doc § 4.2.1: icon, name, vendor, short desc, badges, rating, download count.
 */

import Link from "next/link";
import type { AppItem } from "@/lib/api";
import { SystemBadge } from "./SystemBadge";
import { StatusBadge } from "./StatusBadge";

// Fallback icon: gray placeholder with first letter
function AppIcon({ name, size = 64 }: { name: string; size?: number }) {
  const initial = name.charAt(0).toUpperCase();
  return (
    <div
      className="bg-gray-200 rounded-lg flex items-center justify-center text-gray-500 font-bold flex-shrink-0"
      style={{ width: size, height: size, fontSize: size * 0.4 }}
      aria-hidden="true"
    >
      {initial}
    </div>
  );
}

function StarRating({ rating }: { rating: number | null }) {
  if (rating === null) return <span className="text-xs text-gray-400">No rating</span>;
  return (
    <span className="text-xs text-yellow-600" aria-label={`Rating: ${rating} out of 5`}>
      {"★".repeat(Math.round(rating))}
      {"☆".repeat(5 - Math.round(rating))} {rating.toFixed(1)}
    </span>
  );
}

export function AppCard({ app }: { app: AppItem }) {
  // Truncate name at 80 chars per design review
  const displayName =
    app.name.length > 80 ? app.name.slice(0, 77) + "..." : app.name;

  return (
    <Link
      href={`/apps/${app.app_id}`}
      className="block border border-gray-200 rounded-xl p-4 hover:shadow-md hover:border-gray-300 transition-shadow bg-white"
    >
      <div className="flex gap-3">
        <AppIcon name={app.name} />
        <div className="min-w-0 flex-1">
          <h3
            className="font-semibold text-gray-900 truncate"
            title={app.name}
          >
            {displayName}
          </h3>
          {app.vendor_name && (
            <p className="text-xs text-gray-500">{app.vendor_name}</p>
          )}
        </div>
      </div>

      <p className="mt-2 text-sm text-gray-600 line-clamp-2">
        {app.description_short || "No description"}
      </p>

      <div className="mt-3 flex flex-wrap gap-1">
        {app.systems?.map((s) => <SystemBadge key={s} system={s} />)}
        <StatusBadge status={app.status} />
      </div>

      <div className="mt-2 flex items-center justify-between text-xs text-gray-500">
        <StarRating rating={app.rating_avg} />
        <span>{app.download_count.toLocaleString()} downloads</span>
      </div>
    </Link>
  );
}
