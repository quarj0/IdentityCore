import {
  Activity,
  AlertTriangle,
  BarChart3,
  BrainCircuit,
  Building2,
  CreditCard,
  FileCheck2,
  FileText,
  Flag,
  Headphones,
  LayoutDashboard,
  Lock,
  Network,
  Server,
  Settings,
  ShieldCheck,
  Users,
  Workflow,
} from "lucide-react";

export const platformNavItems = [
  {
    label: "Dashboard",
    href: "/",
    icon: LayoutDashboard,
  },
  {
    label: "Organizations",
    href: "/organizations",
    icon: Building2,
  },
  {
    label: "Tenants",
    href: "/tenants",
    icon: Server,
  },
  {
    label: "Users",
    href: "/users",
    icon: Users,
  },
  {
    label: "Templates",
    href: "/templates",
    icon: FileText,
  },
  {
    label: "Workflows",
    href: "/workflows",
    icon: Workflow,
  },
  {
    label: "AI Providers",
    href: "/ai-providers",
    icon: BrainCircuit,
  },
  {
    label: "Verification Providers",
    href: "/providers",
    icon: Network,
  },
  {
    label: "Manual Review",
    href: "/review",
    icon: FileCheck2,
  },
  {
    label: "Compliance",
    href: "/compliance",
    icon: ShieldCheck,
  },
  {
    label: "Billing",
    href: "/billing",
    icon: CreditCard,
  },
  {
    label: "Analytics",
    href: "/analytics",
    icon: BarChart3,
  },
  {
    label: "Feature Flags",
    href: "/feature-flags",
    icon: Flag,
  },
  {
    label: "Incidents",
    href: "/incidents",
    icon: AlertTriangle,
  },
  {
    label: "Support",
    href: "/support",
    icon: Headphones,
  },
  {
    label: "Security",
    href: "/security",
    icon: Lock,
  },
  {
    label: "Audit",
    href: "/audit",
    icon: Activity,
  },
  {
    label: "Settings",
    href: "/settings",
    icon: Settings,
  },
] as const;
