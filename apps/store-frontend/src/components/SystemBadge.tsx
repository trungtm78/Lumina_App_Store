/**
 * System badge — colored label for Core/Plus/Storage/Care.
 */

const SYSTEM_COLORS: Record<string, string> = {
  core: "bg-blue-100 text-blue-800",
  plus: "bg-purple-100 text-purple-800",
  storage: "bg-green-100 text-green-800",
  care: "bg-orange-100 text-orange-800",
  all: "bg-gray-100 text-gray-800",
};

export function SystemBadge({ system }: { system: string }) {
  const colors = SYSTEM_COLORS[system] || "bg-gray-100 text-gray-700";
  return (
    <span
      className={`inline-block px-2 py-0.5 rounded text-xs font-medium uppercase ${colors}`}
    >
      {system}
    </span>
  );
}
