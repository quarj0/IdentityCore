import {
  ClipboardList,
  FileCheck2,
  LayoutDashboard,
  KeyRound,
  ShieldCheck,
  Webhook,
} from "lucide-react";

export const platformNavItems = [
  {
    label: "Dashboard",
    href: "/dashboard",
    icon: LayoutDashboard,
  },
  {
    label: "Organization Review",
    href: "/review",
    icon: FileCheck2,
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
] as const;
