/**
 * Status badge — Installed/Available/Featured.
 */

const STATUS_STYLES: Record<string, string> = {
  approved: "bg-green-100 text-green-800",
  installed: "bg-green-100 text-green-800",
  submitted: "bg-yellow-100 text-yellow-800",
  reviewing: "bg-yellow-100 text-yellow-800",
  draft: "bg-gray-100 text-gray-600",
  rejected: "bg-red-100 text-red-800",
};

const STATUS_LABELS: Record<string, string> = {
  approved: "Available",
  installed: "Installed",
  submitted: "Pending",
  reviewing: "Under Review",
  draft: "Draft",
  rejected: "Rejected",
};

export function StatusBadge({ status }: { status: string }) {
  const style = STATUS_STYLES[status] || "bg-gray-100 text-gray-600";
  const label = STATUS_LABELS[status] || status;
  return (
    <span
      className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${style}`}
      role="status"
      aria-label={`Status: ${label}`}
    >
      {label}
    </span>
  );
}
