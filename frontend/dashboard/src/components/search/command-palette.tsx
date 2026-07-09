"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Search } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  Input,
} from "@identitycore/ui";

const actions = [
  ["Create project", "/projects/new"],
  ["Create workflow", "/workflows/new"],
  ["Invite member", "/team/invite"],
  ["Add webhook", "/webhooks/new"],
  ["Create API key", "/api-keys/new"],
  ["Projects", "/projects"],
  ["Workflows", "/workflows"],
  ["Templates", "/templates"],
  ["Manual review", "/manual-review"],
  ["Settings", "/settings"],
  ["Documentation", "http://localhost:3003"],
];

export function CommandPalette() {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");

  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setOpen(true);
      }
    }

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  const filtered = actions.filter(([label]) =>
    label.toLowerCase().includes(query.toLowerCase()),
  );

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogContent className="rounded-3xl">
        <DialogHeader>
          <DialogTitle>Search dashboard</DialogTitle>
        </DialogHeader>

        <div className="relative">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <Input
            autoFocus
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search pages..."
            className="pl-9"
          />
        </div>

        <div className="grid gap-1">
          {filtered.map(([label, href]) => (
            <Link
              key={href}
              href={href}
              onClick={() => setOpen(false)}
              className="rounded-xl px-3 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100 hover:text-slate-950"
            >
              {label}
            </Link>
          ))}
        </div>
      </DialogContent>
    </Dialog>
  );
}
