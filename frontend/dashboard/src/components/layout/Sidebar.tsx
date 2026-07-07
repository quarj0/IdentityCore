"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  ShieldCheck,
  FileText,
  Users,
  ClipboardCheck,
  Settings2,
  KeyRound,
  Webhook,
  ScrollText,
  Building2,
  UserCog,
  Receipt,
  Settings,
  ChevronDown,
  ChevronRight,
  PanelLeftClose,
  PanelLeft,
  Fingerprint,
} from "lucide-react";
import { cn } from "@identitycore/ui";

/* ─── Nav structure ────────────────────────────────────── */
type NavItem = {
  label: string;
  href?: string;
  icon: React.ElementType;
  children?: Omit<NavItem, "children" | "icon">[];
};

const NAV: NavItem[] = [
  {
    label: "Overview",
    href: "/overview",
    icon: LayoutDashboard,
  },
  {
    label: "Verifications",
    icon: ShieldCheck,
    children: [
      { label: "Requests", href: "/verifications/requests" },
      { label: "Subjects", href: "/verifications/subjects" },
      { label: "Manual Review", href: "/verifications/review" },
      { label: "Policies", href: "/verifications/policies" },
    ],
  },
  {
    label: "Developers",
    icon: KeyRound,
    children: [
      { label: "API Keys", href: "/developers/api-keys" },
      { label: "Webhooks", href: "/developers/webhooks" },
      { label: "Logs", href: "/developers/logs" },
    ],
  },
  {
    label: "Organization",
    icon: Building2,
    children: [
      { label: "Team", href: "/organization/team" },
      { label: "Audit Logs", href: "/organization/audit-logs" },
      { label: "Billing", href: "/organization/billing" },
      { label: "Settings", href: "/organization/settings" },
    ],
  },
];

/* ─── Item icon map for children ──────────────────────── */
const CHILD_ICONS: Record<string, React.ElementType> = {
  Requests: FileText,
  Subjects: Users,
  "Manual Review": ClipboardCheck,
  Policies: Settings2,
  "API Keys": KeyRound,
  Webhooks: Webhook,
  Logs: ScrollText,
  Team: UserCog,
  "Audit Logs": ScrollText,
  Billing: Receipt,
  Settings: Settings,
};

/* ─── Sidebar ─────────────────────────────────────────── */
export function Sidebar() {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);
  const [openSections, setOpenSections] = useState<Record<string, boolean>>({
    Verifications: true,
    Developers: false,
    Organization: false,
  });

  function toggleSection(label: string) {
    setOpenSections((prev) => ({ ...prev, [label]: !prev[label] }));
  }

  function isActive(href: string) {
    return pathname === href || pathname.startsWith(href + "/");
  }

  return (
    <aside
      className={cn(
        "flex h-full flex-col border-r border-sidebar-border bg-sidebar transition-[width] duration-200 ease-in-out",
        collapsed ? "w-[60px]" : "w-[240px]"
      )}
    >
      {/* Logo */}
      <div
        className={cn(
          "flex h-[60px] shrink-0 items-center gap-2.5 border-b border-sidebar-border px-4",
          collapsed && "justify-center px-0"
        )}
      >
        <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-white/10">
          <Fingerprint className="h-4 w-4 text-white" strokeWidth={1.75} />
        </div>
        {!collapsed && (
          <span className="text-sm font-semibold tracking-tight text-white">
            IdentityCore
          </span>
        )}
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto p-2 space-y-0.5">
        {NAV.map((item) => {
          const Icon = item.icon;

          /* Top-level link */
          if (item.href) {
            const active = isActive(item.href);
            return (
              <Link
                key={item.label}
                href={item.href}
                title={collapsed ? item.label : undefined}
                className={cn(
                  "flex h-8 items-center gap-2.5 rounded-md px-2 text-sm transition-colors",
                  active
                    ? "bg-sidebar-accent text-sidebar-accent-foreground font-medium"
                    : "text-sidebar-foreground hover:bg-sidebar-accent/60 hover:text-sidebar-accent-foreground"
                )}
              >
                <Icon className="h-4 w-4 shrink-0" strokeWidth={1.75} />
                {!collapsed && <span>{item.label}</span>}
              </Link>
            );
          }

          /* Collapsible section */
          const isOpen = openSections[item.label];
          const hasActiveChild = item.children?.some(
            (c) => c.href && isActive(c.href)
          );

          return (
            <div key={item.label}>
              <button
                onClick={() => !collapsed && toggleSection(item.label)}
                title={collapsed ? item.label : undefined}
                className={cn(
                  "flex h-8 w-full items-center gap-2.5 rounded-md px-2 text-sm transition-colors",
                  hasActiveChild
                    ? "text-sidebar-accent-foreground"
                    : "text-sidebar-foreground hover:bg-sidebar-accent/60 hover:text-sidebar-accent-foreground"
                )}
              >
                <Icon className="h-4 w-4 shrink-0" strokeWidth={1.75} />
                {!collapsed && (
                  <>
                    <span className="flex-1 text-left">{item.label}</span>
                    {isOpen ? (
                      <ChevronDown className="h-3.5 w-3.5 opacity-60" />
                    ) : (
                      <ChevronRight className="h-3.5 w-3.5 opacity-60" />
                    )}
                  </>
                )}
              </button>

              {/* Children */}
              {!collapsed && isOpen && (
                <div className="ml-4 mt-0.5 space-y-0.5 border-l border-sidebar-border pl-3">
                  {item.children?.map((child) => {
                    const ChildIcon = CHILD_ICONS[child.label];
                    const active = child.href ? isActive(child.href) : false;
                    return (
                      <Link
                        key={child.label}
                        href={child.href ?? "#"}
                        className={cn(
                          "flex h-8 items-center gap-2 rounded-md px-2 text-sm transition-colors",
                          active
                            ? "bg-sidebar-accent text-sidebar-accent-foreground font-medium"
                            : "text-sidebar-foreground/80 hover:bg-sidebar-accent/60 hover:text-sidebar-accent-foreground"
                        )}
                      >
                        {ChildIcon && (
                          <ChildIcon
                            className="h-3.5 w-3.5 shrink-0"
                            strokeWidth={1.75}
                          />
                        )}
                        <span>{child.label}</span>
                      </Link>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })}
      </nav>

      {/* Collapse toggle */}
      <div className="shrink-0 border-t border-sidebar-border p-2">
        <button
          onClick={() => setCollapsed((v) => !v)}
          title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          className="flex h-8 w-full items-center justify-center gap-2 rounded-md text-sidebar-foreground/60 transition-colors hover:bg-sidebar-accent/60 hover:text-sidebar-accent-foreground"
        >
          {collapsed ? (
            <PanelLeft className="h-4 w-4" />
          ) : (
            <>
              <PanelLeftClose className="h-4 w-4" />
              <span className="text-xs">Collapse</span>
            </>
          )}
        </button>
      </div>
    </aside>
  );
}
