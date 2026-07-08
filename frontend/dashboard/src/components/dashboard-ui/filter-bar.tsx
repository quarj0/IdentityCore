import { Search } from "lucide-react";
import { Button, Input } from "@identitycore/ui";

interface FilterBarProps {
  searchPlaceholder?: string;
  actionLabel?: string;
}

export function FilterBar({
  searchPlaceholder = "Search...",
  actionLabel,
}: FilterBarProps) {
  return (
    <div className="flex flex-col gap-3 rounded-3xl border border-slate-200 bg-white p-4 shadow-sm sm:flex-row sm:items-center sm:justify-between">
      <div className="relative w-full sm:max-w-sm">
        <Search
          className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400"
          aria-hidden="true"
        />
        <Input
          placeholder={searchPlaceholder}
          className="h-11 rounded-2xl pl-10"
          aria-label={searchPlaceholder}
        />
      </div>

      {actionLabel ? (
        <Button className="rounded-xl">{actionLabel}</Button>
      ) : null}
    </div>
  );
}
