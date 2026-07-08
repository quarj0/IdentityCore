"use client";

import Link from "next/link";
import { Menu } from "lucide-react";
import { useState } from "react";
import { Button, Sheet, SheetContent, SheetTrigger } from "@identitycore/ui";
import { dashboardNav } from "@/data/dashboard-nav";

export function MobileSidebar() {
  const [open, setOpen] = useState(false);

  return (
    <div className="lg:hidden">
      <Sheet open={open} onOpenChange={setOpen}>
        <SheetTrigger asChild>
          <Button variant="ghost" size="icon" aria-label="Open dashboard menu">
            <Menu className="h-5 w-5" />
          </Button>
        </SheetTrigger>

        <SheetContent side="left" className="w-80 overflow-y-auto">
          <div className="py-4">
            <p className="text-sm font-semibold">IdentityCore</p>
            <p className="text-xs text-muted-foreground">Workspace dashboard</p>
          </div>

          <nav className="space-y-6">
            {dashboardNav.map((group) => (
              <div key={group.title}>
                <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                  {group.title}
                </p>

                <div className="mt-2 grid gap-1">
                  {group.items.map((item) => {
                    const Icon = item.icon;

                    return (
                      <Link
                        key={item.href}
                        href={item.href}
                        onClick={() => setOpen(false)}
                        className="flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium text-muted-foreground hover:bg-accent hover:text-foreground"
                      >
                        <Icon className="h-4 w-4 text-blue-600" />
                        {item.label}
                      </Link>
                    );
                  })}
                </div>
              </div>
            ))}
          </nav>
        </SheetContent>
      </Sheet>
    </div>
  );
}
