import { Bell, Search } from "lucide-react";
import { Avatar, AvatarFallback, Badge, Button } from "@identitycore/ui";

export function DashboardTopbar() {
  return (
    <header className="sticky top-0 z-40 border-b border-slate-200 bg-white/95 backdrop-blur">
      <div className="flex h-16 items-center gap-4 px-4 sm:px-6">
        <div className="relative hidden flex-1 sm:block">
          <Search
            className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400"
            aria-hidden="true"
          />
          <input
            type="search"
            placeholder="Search workflows, requests, subjects..."
            aria-label="Search dashboard"
            className="h-10 w-full max-w-md rounded-xl border border-slate-200 bg-slate-50 pl-10 pr-4 text-sm outline-none focus:border-blue-600 focus:ring-2 focus:ring-blue-100"
          />
        </div>

        <div className="ml-auto flex items-center gap-3">
          <Badge variant="secondary" className="rounded-full">
            Sandbox
          </Badge>

          <Button variant="ghost" size="icon" aria-label="Notifications">
            <Bell className="h-4 w-4" aria-hidden="true" />
          </Button>

          <Avatar>
            <AvatarFallback>KA</AvatarFallback>
          </Avatar>
        </div>
      </div>
    </header>
  );
}
