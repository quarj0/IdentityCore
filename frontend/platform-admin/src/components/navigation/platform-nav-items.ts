import {
  BarChart3,
  Building2,
  ClipboardList,
  FileCheck2,
  Flag,
  Headphones,
  Landmark,
  LayoutDashboard,
  KeyRound,
  ReceiptText,
  Settings2,
  ShieldCheck,
  Siren,
  Sparkles,
  UsersRound,
  Webhook,
  Workflow,
} from "lucide-react";

export const platformNavItems = [
  {
    label: "Dashboard",
    href: "/",
    icon: LayoutDashboard,
  },
  {
    label: "Organization Review",
    href: "/review",
    icon: FileCheck2,
  },
  {
    label: "Organizations",
    href: "/organizations",
    icon: Building2,
  },
  {
    label: "Tenants",
    href: "/tenants",
    icon: Landmark,
  },
  {
    label: "Platform access",
    href: "/users",
    icon: UsersRound,
  },
  {
    label: "Verification Providers",
    href: "/providers",
    icon: ShieldCheck,
  },
  {
    label: "Compliance",
    href: "/compliance",
    icon: ShieldCheck,
  },
  {
    label: "Audit",
    href: "/audit",
    icon: ClipboardList,
  },
  {
    label: "API Clients",
    href: "/api-clients",
    icon: KeyRound,
  },
  {
    label: "Webhooks",
    href: "/webhooks",
    icon: Webhook,
  },
  {
    label: "Workflows",
    href: "/workflows",
    icon: Workflow,
  },
  {
    label: "Templates",
    href: "/templates",
    icon: FileCheck2,
  },
  {
    label: "AI providers",
    href: "/ai-providers",
    icon: Sparkles,
  },
  {
    label: "Billing",
    href: "/billing",
    icon: ReceiptText,
  },
  {
    label: "Analytics",
    href: "/analytics",
    icon: BarChart3,
  },
  {
    label: "Incidents",
    href: "/incidents",
    icon: Siren,
  },
  {
    label: "Security",
    href: "/security",
    icon: ShieldCheck,
  },
  {
    label: "Support",
    href: "/support",
    icon: Headphones,
  },
  {
    label: "Feature flags",
    href: "/feature-flags",
    icon: Flag,
  },
  {
    label: "Settings",
    href: "/settings",
    icon: Settings2,
  },
] as const;
