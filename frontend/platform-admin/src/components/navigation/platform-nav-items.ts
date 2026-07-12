import { FileCheck2, LayoutDashboard } from "lucide-react";

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
] as const;
