import { Badge } from "@identitycore/ui";

export function StatusBadge({ status }: { status: string }) {
  const normalized = status.toLowerCase();

  const className =
    normalized.includes("active") ||
    normalized.includes("complete") ||
    normalized.includes("approved")
      ? "bg-blue-50 text-blue-700 ring-1 ring-blue-100"
      : normalized.includes("pending") ||
          normalized.includes("review") ||
          normalized.includes("current")
        ? "bg-amber-50 text-amber-700 ring-1 ring-amber-100"
        : normalized.includes("failed") ||
            normalized.includes("rejected") ||
            normalized.includes("disabled")
          ? "bg-red-50 text-red-700 ring-1 ring-red-100"
          : "bg-slate-100 text-slate-700 ring-1 ring-slate-200";

  return <Badge className={`rounded-full ${className}`}>{status}</Badge>;
}
