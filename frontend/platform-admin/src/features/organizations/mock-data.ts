export type OrganizationStatus =
  | "active"
  | "pending_review"
  | "suspended"
  | "rejected"
  | "deleted";

export type OrganizationPlan = "starter" | "growth" | "enterprise";

export type OrganizationRiskLevel = "low" | "medium" | "high" | "critical";

export type Organization = {
  id: string;
  name: string;
  slug: string;
  industry: string;
  country: string;
  status: OrganizationStatus;
  plan: OrganizationPlan;
  riskLevel: OrganizationRiskLevel;
  riskScore: number;
  verificationsThisMonth: number;
  apiRequestsThisMonth: number;
  createdAt: string;
  lastActiveAt: string;
  ownerName: string;
  ownerEmail: string;
  domain: string;
  region: string;
  monthlySpend: string;
  brandingColor: string;
  logoInitials: string;
};

export const organizations: Organization[] = [
  {
    id: "org_ghana_fintrust",
    name: "Ghana FinTrust Bank",
    slug: "ghana-fintrust-bank",
    industry: "Financial institution",
    country: "Ghana",
    status: "active",
    plan: "enterprise",
    riskLevel: "low",
    riskScore: 18,
    verificationsThisMonth: 48210,
    apiRequestsThisMonth: 1840000,
    createdAt: "2026-02-12",
    lastActiveAt: "2026-07-09 08:14",
    ownerName: "Ama Mensah",
    ownerEmail: "ama.mensah@fintrust.example",
    domain: "verify.fintrust.example",
    region: "Africa West",
    monthlySpend: "$12,840",
    brandingColor: "#22d3ee",
    logoInitials: "GF",
  },
  {
    id: "org_lagos_pay",
    name: "LagosPay",
    slug: "lagospay",
    industry: "Fintech",
    country: "Nigeria",
    status: "active",
    plan: "growth",
    riskLevel: "medium",
    riskScore: 42,
    verificationsThisMonth: 31490,
    apiRequestsThisMonth: 970000,
    createdAt: "2026-03-08",
    lastActiveAt: "2026-07-09 07:44",
    ownerName: "Tunde Adebayo",
    ownerEmail: "tunde@lagospay.example",
    domain: "kyc.lagospay.example",
    region: "Africa West",
    monthlySpend: "$8,210",
    brandingColor: "#34d399",
    logoInitials: "LP",
  },
  {
    id: "org_civic_registry",
    name: "Civic Registry Authority",
    slug: "civic-registry-authority",
    industry: "Government",
    country: "Kenya",
    status: "pending_review",
    plan: "enterprise",
    riskLevel: "medium",
    riskScore: 51,
    verificationsThisMonth: 0,
    apiRequestsThisMonth: 0,
    createdAt: "2026-07-01",
    lastActiveAt: "2026-07-08 17:22",
    ownerName: "Grace Wanjiku",
    ownerEmail: "grace@civic-registry.example",
    domain: "identity.civic-registry.example",
    region: "Africa East",
    monthlySpend: "$0",
    brandingColor: "#818cf8",
    logoInitials: "CR",
  },
  {
    id: "org_eduverify",
    name: "EduVerify Africa",
    slug: "eduverify-africa",
    industry: "Education",
    country: "Ghana",
    status: "active",
    plan: "starter",
    riskLevel: "low",
    riskScore: 24,
    verificationsThisMonth: 8720,
    apiRequestsThisMonth: 244000,
    createdAt: "2026-04-19",
    lastActiveAt: "2026-07-09 06:02",
    ownerName: "Kojo Boateng",
    ownerEmail: "kojo@eduverify.example",
    domain: "verify.eduverify.example",
    region: "Africa West",
    monthlySpend: "$1,420",
    brandingColor: "#facc15",
    logoInitials: "EA",
  },
  {
    id: "org_healthpass",
    name: "HealthPass Clinics",
    slug: "healthpass-clinics",
    industry: "Healthcare",
    country: "South Africa",
    status: "suspended",
    plan: "growth",
    riskLevel: "critical",
    riskScore: 91,
    verificationsThisMonth: 1290,
    apiRequestsThisMonth: 87000,
    createdAt: "2026-01-27",
    lastActiveAt: "2026-07-04 11:10",
    ownerName: "Nandi Khumalo",
    ownerEmail: "nandi@healthpass.example",
    domain: "identity.healthpass.example",
    region: "Africa South",
    monthlySpend: "$620",
    brandingColor: "#fb7185",
    logoInitials: "HC",
  },
  {
    id: "org_borderless_jobs",
    name: "Borderless Jobs",
    slug: "borderless-jobs",
    industry: "Enterprise",
    country: "United Kingdom",
    status: "active",
    plan: "enterprise",
    riskLevel: "high",
    riskScore: 73,
    verificationsThisMonth: 22140,
    apiRequestsThisMonth: 720000,
    createdAt: "2026-05-15",
    lastActiveAt: "2026-07-09 05:51",
    ownerName: "Sarah Mitchell",
    ownerEmail: "sarah@borderlessjobs.example",
    domain: "verify.borderlessjobs.example",
    region: "Europe West",
    monthlySpend: "$6,430",
    brandingColor: "#38bdf8",
    logoInitials: "BJ",
  },
];

export const organizationUsage = {
  verificationsLimit: 100000,
  verificationsUsed: 48210,
  apiLimit: 3000000,
  apiUsed: 1840000,
  storageLimitGb: 500,
  storageUsedGb: 184,
  reviewers: 24,
  templates: 18,
};

export const organizationDomains = [
  {
    domain: "verify.fintrust.example",
    type: "Verification portal",
    status: "Verified",
    ssl: "Active",
  },
  {
    domain: "api.fintrust.example",
    type: "API",
    status: "Verified",
    ssl: "Active",
  },
  {
    domain: "callbacks.fintrust.example",
    type: "Webhooks",
    status: "Pending DNS",
    ssl: "Pending",
  },
];

export const organizationSubscription = {
  plan: "Enterprise",
  billingCycle: "Monthly",
  renewalDate: "2026-08-12",
  currentUsageCost: "$12,840",
  baseFee: "$4,000",
  usageFee: "$8,840",
  paymentStatus: "Paid",
};

export const organizationBranding = {
  primaryColor: "#22d3ee",
  logoStatus: "Uploaded",
  portalTheme: "Dark",
  customEmailSender: "verification@fintrust.example",
  brandReview: "Approved",
};
