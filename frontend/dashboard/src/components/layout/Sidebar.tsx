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
  Fingerprint,
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
import { cn } from "@identitycore/ui";

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
        "sticky top-0 flex h-screen flex-col border-r border-sidebar-border bg-sidebar transition-[width] duration-200 ease-in-out",
        collapsed ? "w-[68px]" : "w-[264px]"
      )}
    >
      <div
        className={cn("flex h-[72px] shrink-0 items-center gap-3 border-b border-sidebar-border px-4", collapsed && "justify-center px-0")}
      >
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-white/10 shadow-inner">
          <Fingerprint className="h-4.5 w-4.5 text-white" strokeWidth={1.75} />
        </div>
        {!collapsed ? (
          <div>
            <div className="text-sm font-semibold tracking-[0.16em] text-white">
              IDENTITYCORE
            </div>
            <div className="text-xs text-sidebar-foreground/80">Team dashboard</div>
          </div>
        ) : null}
      </div>

      <nav className="flex-1 overflow-y-auto p-3 space-y-1">
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
                  "flex h-10 items-center gap-2.5 rounded-xl px-3 text-sm transition-colors",
                  active
                    ? "bg-sidebar-accent text-sidebar-accent-foreground font-medium"
                    : "text-sidebar-foreground hover:bg-sidebar-accent/60 hover:text-sidebar-accent-foreground"
                )}
              >
                <Icon className="h-4 w-4 shrink-0" strokeWidth={1.75} />
                {!collapsed ? <span>{item.label}</span> : null}
              </Link>
            );
          }

          const isOpen = openSections[item.label];
          const hasActiveChild = item.children?.some((child) => child.href && isActive(child.href));

          return (
            <div key={item.label}>
              <button
                onClick={() => !collapsed && toggleSection(item.label)}
                title={collapsed ? item.label : undefined}
                className={cn(
                  "flex h-10 w-full items-center gap-2.5 rounded-xl px-3 text-sm transition-colors",
                  hasActiveChild
                    ? "text-sidebar-accent-foreground"
                    : "text-sidebar-foreground hover:bg-sidebar-accent/60 hover:text-sidebar-accent-foreground"
                )}
              >
                <Icon className="h-4 w-4 shrink-0" strokeWidth={1.75} />
                {!collapsed ? (
                  <>
                    <span className="flex-1 text-left">{item.label}</span>
                    {isOpen ? (
                      <ChevronDown className="h-3.5 w-3.5 opacity-60" />
                    ) : (
                      <ChevronRight className="h-3.5 w-3.5 opacity-60" />
                    )}
                  </>
                ) : null}
              </button>

              {!collapsed && isOpen ? (
                <div className="ml-4 mt-1 space-y-1 border-l border-sidebar-border pl-3">
                  {item.children?.map((child) => {
                    const ChildIcon = CHILD_ICONS[child.label];
                    const active = child.href ? isActive(child.href) : false;
                    return (
                      <Link
                        key={child.label}
                        href={child.href ?? "#"}
                        className={cn(
                          "flex h-9 items-center gap-2 rounded-xl px-2.5 text-sm transition-colors",
                          active
                            ? "bg-sidebar-accent text-sidebar-accent-foreground font-medium"
                            : "text-sidebar-foreground/80 hover:bg-sidebar-accent/60 hover:text-sidebar-accent-foreground"
                        )}
                      >
                        {ChildIcon ? (
                          <ChildIcon className="h-3.5 w-3.5 shrink-0" strokeWidth={1.75} />
                        ) : null}
                        <span>{child.label}</span>
                      </Link>
                    );
                  })}
                </div>
              ) : null}
            </div>
          );
        })}
      </nav>

      <div className="shrink-0 border-t border-sidebar-border p-3">
        <button
          onClick={() => setCollapsed((value) => !value)}
          title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          className="flex h-10 w-full items-center justify-center gap-2 rounded-xl text-sidebar-foreground/60 transition-colors hover:bg-sidebar-accent/60 hover:text-sidebar-accent-foreground"
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
