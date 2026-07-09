export type AdminStatus = "active" | "invited" | "disabled" | "locked";
export type AdminRole =
  | "Platform Owner"
  | "Security Admin"
  | "Compliance Admin"
  | "Support Lead"
  | "Billing Admin"
  | "Read Only";

export type AdminUser = {
  id: string;
  name: string;
  email: string;
  initials: string;
  status: AdminStatus;
  role: AdminRole;
  department: string;
  location: string;
  lastActiveAt: string;
  joinedAt: string;
  mfaEnabled: boolean;
  ssoEnabled: boolean;
  activeSessions: number;
  permissionsCount: number;
  riskLevel: "Low" | "Medium" | "High";
};

export const adminUsers: AdminUser[] = [
  {
    id: "admin_kwadwo",
    name: "Kwadwo Owusu Ansah",
    email: "kwadwo@identitycore.example",
    initials: "KO",
    status: "active",
    role: "Platform Owner",
    department: "Platform",
    location: "Ghana",
    lastActiveAt: "2026-07-09 09:42",
    joinedAt: "2026-01-18",
    mfaEnabled: true,
    ssoEnabled: true,
    activeSessions: 3,
    permissionsCount: 42,
    riskLevel: "Low",
  },
  {
    id: "admin_ama",
    name: "Ama Mensah",
    email: "ama@identitycore.example",
    initials: "AM",
    status: "active",
    role: "Compliance Admin",
    department: "Compliance",
    location: "Ghana",
    lastActiveAt: "2026-07-09 08:20",
    joinedAt: "2026-02-04",
    mfaEnabled: true,
    ssoEnabled: true,
    activeSessions: 2,
    permissionsCount: 28,
    riskLevel: "Low",
  },
  {
    id: "admin_tunde",
    name: "Tunde Adebayo",
    email: "tunde@identitycore.example",
    initials: "TA",
    status: "active",
    role: "Security Admin",
    department: "Security",
    location: "Nigeria",
    lastActiveAt: "2026-07-09 07:55",
    joinedAt: "2026-03-11",
    mfaEnabled: true,
    ssoEnabled: true,
    activeSessions: 1,
    permissionsCount: 36,
    riskLevel: "Medium",
  },
  {
    id: "admin_sarah",
    name: "Sarah Mitchell",
    email: "sarah@identitycore.example",
    initials: "SM",
    status: "invited",
    role: "Support Lead",
    department: "Support",
    location: "United Kingdom",
    lastActiveAt: "Never",
    joinedAt: "Pending",
    mfaEnabled: false,
    ssoEnabled: false,
    activeSessions: 0,
    permissionsCount: 14,
    riskLevel: "Low",
  },
  {
    id: "admin_grace",
    name: "Grace Wanjiku",
    email: "grace@identitycore.example",
    initials: "GW",
    status: "disabled",
    role: "Read Only",
    department: "Operations",
    location: "Kenya",
    lastActiveAt: "2026-06-28 14:11",
    joinedAt: "2026-01-30",
    mfaEnabled: true,
    ssoEnabled: true,
    activeSessions: 0,
    permissionsCount: 6,
    riskLevel: "High",
  },
];

export const adminPermissions = [
  {
    group: "Organizations",
    permissions: [
      "View organizations",
      "Approve onboarding",
      "Suspend organizations",
      "Reactivate organizations",
      "Delete organizations",
    ],
  },
  {
    group: "Security",
    permissions: [
      "View threat events",
      "Manage blocked IPs",
      "Review suspicious logins",
      "Configure rate limits",
    ],
  },
  {
    group: "Compliance",
    permissions: [
      "Manage retention policies",
      "Export audit logs",
      "Review consent records",
      "Manage supported countries",
    ],
  },
  {
    group: "Billing",
    permissions: [
      "View subscriptions",
      "View invoices",
      "Adjust platform fees",
    ],
  },
];

export const adminSessions = [
  {
    id: "sess_001",
    device: "Chrome on Ubuntu",
    location: "Accra, Ghana",
    ipAddress: "197.251.xxx.xxx",
    lastSeen: "Now",
    status: "Current",
  },
  {
    id: "sess_002",
    device: "Safari on iPhone",
    location: "Accra, Ghana",
    ipAddress: "102.176.xxx.xxx",
    lastSeen: "2 hours ago",
    status: "Active",
  },
  {
    id: "sess_003",
    device: "Firefox on Windows",
    location: "Kumasi, Ghana",
    ipAddress: "154.160.xxx.xxx",
    lastSeen: "Yesterday",
    status: "Expired",
  },
];

export const adminActivity = [
  {
    id: "act_001",
    action: "Approved organization onboarding",
    target: "Ghana FinTrust Bank",
    time: "18 minutes ago",
    severity: "Info",
  },
  {
    id: "act_002",
    action: "Updated AI provider failover priority",
    target: "PaddleOCR Pool",
    time: "1 hour ago",
    severity: "Warning",
  },
  {
    id: "act_003",
    action: "Exported audit logs",
    target: "Platform audit",
    time: "3 hours ago",
    severity: "Info",
  },
  {
    id: "act_004",
    action: "Disabled stale admin session",
    target: "Firefox on Windows",
    time: "Yesterday",
    severity: "Success",
  },
];

export function getAdminUserById(userId: string) {
  return adminUsers.find((user) => user.id === userId);
}
