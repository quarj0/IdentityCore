import {
  Bell,
  Building2,
  FileCheck2,
  FileText,
  KeyRound,
  LayoutDashboard,
  ListChecks,
  ScrollText,
  Settings,
  ShieldCheck,
  Users,
  Webhook,
  Workflow,
} from "lucide-react";

export const dashboardNav = [
  {
    title: "Workspace",
    items: [
      {
        href: "/",
        label: "Overview",
        icon: LayoutDashboard,
      },
      {
        href: "/onboarding",
        label: "Approval status",
        icon: ListChecks,
      },
      {
        href: "/projects",
        label: "Projects",
        icon: Building2,
      },
      {
        href: "/notifications",
        label: "Notifications",
        icon: Bell,
      },
    ],
  },
  {
    title: "Identity workflows",
    items: [
      {
        href: "/workflows",
        label: "Workflows",
        icon: Workflow,
      },
      {
        href: "/templates",
        label: "Templates",
        icon: FileText,
      },
      {
        href: "/verification-requests",
        label: "Verification requests",
        icon: FileCheck2,
      },
      {
        href: "/subjects",
        label: "Subjects",
        icon: Users,
      },
      {
        href: "/manual-review",
        label: "Manual review",
        icon: ShieldCheck,
      },
    ],
  },
  {
    title: "Developers",
    items: [
      {
        href: "/api-keys",
        label: "API keys",
        icon: KeyRound,
      },
      {
        href: "/webhooks",
        label: "Webhooks",
        icon: Webhook,
      },
      {
        href: "/audit-logs",
        label: "Audit logs",
        icon: ScrollText,
      },
    ],
  },
  {
    title: "Organization",
    items: [
      {
        href: "/team",
        label: "Team",
        icon: Users,
      },
      {
        href: "/settings",
        label: "Settings",
        icon: Settings,
      },
    ],
  },
];
