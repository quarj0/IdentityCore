"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Building2,
  ChevronDown,
  ChevronRight,
  ClipboardCheck,
  FileText,
  KeyRound,
  LayoutDashboard,
  PanelLeft,
  PanelLeftClose,
  Receipt,
  ScrollText,
  Settings,
  Settings2,
  ShieldCheck,
  UserCog,
  Users,
  Webhook,
} from "lucide-react";
import { BrandMark, cn, ThemeToggle } from "@identitycore/ui";

type NavItem = {
  label: string;
  href?: string;
  icon: React.ElementType;
  children?: Omit<NavItem, "children" | "icon">[];
};

const NAV: NavItem[] = [
  { label: "Overview", href: "/overview", icon: LayoutDashboard },
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
        "sticky top-0 flex h-screen flex-col border-r border-sidebar-border bg-sidebar",
        collapsed ? "w-[60px]" : "w-60"
      )}
    >
      <div
        className={cn(
          "flex h-14 shrink-0 items-center border-b border-sidebar-border px-4",
          collapsed && "justify-center px-0"
        )}
      >
        {collapsed ? (
          <div className="flex h-8 w-8 items-center justify-center rounded-md bg-primary text-primary-foreground">
            <ShieldCheck className="h-4 w-4" strokeWidth={2} />
          </div>
        ) : (
          <BrandMark subtitle="Dashboard" variant="sidebar" size="md" />
        )}
      </div>

      <nav className="flex-1 overflow-y-auto p-3">
        {NAV.map((item) => {
          const Icon = item.icon;

          if (item.href) {
            const active = isActive(item.href);
            return (
              <Link
                key={item.label}
                href={item.href}
                title={collapsed ? item.label : undefined}
                className={cn(
                  "mb-0.5 flex h-9 items-center gap-2.5 rounded-md px-2.5 text-sm transition-colors",
                  active
                    ? "bg-sidebar-accent font-medium text-sidebar-accent-foreground"
                    : "text-sidebar-muted-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
                )}
              >
                <Icon className="h-4 w-4 shrink-0" strokeWidth={1.75} />
                {!collapsed ? <span>{item.label}</span> : null}
              </Link>
            );
          }

          const isOpen = openSections[item.label];
          const hasActiveChild = item.children?.some(
            (child) => child.href && isActive(child.href)
          );

          return (
            <div key={item.label} className="mb-1">
              {!collapsed ? (
                <p className="mb-1 px-2.5 pt-3 text-[11px] font-medium uppercase tracking-wider text-sidebar-muted-foreground">
                  {item.label}
                </p>
              ) : null}
              {item.children?.map((child) => {
                const active = child.href ? isActive(child.href) : false;
                return (
                  <Link
                    key={child.label}
                    href={child.href ?? "#"}
                    title={collapsed ? child.label : undefined}
                    className={cn(
                      "mb-0.5 flex h-9 items-center gap-2.5 rounded-md px-2.5 text-sm transition-colors",
                      active
                        ? "bg-sidebar-accent font-medium text-sidebar-accent-foreground"
                        : "text-sidebar-muted-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground",
                      collapsed && "justify-center px-0"
                    )}
                  >
                    {!collapsed ? (
                      <>
                        <span className="h-1 w-1 shrink-0 rounded-full bg-current opacity-40" />
                        <span>{child.label}</span>
                      </>
                    ) : (
                      <Icon className="h-4 w-4 shrink-0" strokeWidth={1.75} />
                    )}
                  </Link>
                );
              })}
            </div>
          );
        })}
      </nav>

      <div className="shrink-0 border-t border-sidebar-border p-3">
        <div className={cn("mb-2 flex items-center", collapsed ? "justify-center" : "justify-between")}>
          {!collapsed ? (
            <span className="text-xs text-sidebar-muted-foreground">Theme</span>
          ) : null}
          <ThemeToggle variant="sidebar" />
        </div>
        <button
          onClick={() => setCollapsed((value) => !value)}
          title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          className="flex h-8 w-full items-center justify-center gap-2 rounded-md text-xs text-sidebar-muted-foreground transition-colors hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
        >
          {collapsed ? (
            <PanelLeft className="h-4 w-4" />
          ) : (
            <>
              <PanelLeftClose className="h-3.5 w-3.5" />
              Collapse
            </>
          )}
        </button>
      </div>
    </aside>
  );
}
