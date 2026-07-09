export type TenantStatus =
  | "healthy"
  | "degraded"
  | "maintenance"
  | "provisioning"
  | "offline";

export type TenantRegion =
  | "Africa West"
  | "Africa East"
  | "Africa South"
  | "Europe West"
  | "US East";

export type TenantIsolationModel =
  | "shared"
  | "schema"
  | "database"
  | "dedicated";

export type Tenant = {
  id: string;
  name: string;
  slug: string;
  organizationName: string;
  organizationId: string;
  status: TenantStatus;
  region: TenantRegion;
  isolationModel: TenantIsolationModel;
  databaseName: string;
  databaseStatus: "Healthy" | "Degraded" | "Migrating" | "Offline";
  storageBucket: string;
  storageUsedGb: number;
  storageLimitGb: number;
  apiLatencyMs: number;
  uptime: string;
  activeUsers: number;
  verificationsToday: number;
  createdAt: string;
  lastHealthCheckAt: string;
  environment: "production" | "sandbox" | "staging";
};

export const tenants: Tenant[] = [
  {
    id: "tenant_fintrust_prod",
    name: "FinTrust Production",
    slug: "fintrust-production",
    organizationName: "Ghana FinTrust Bank",
    organizationId: "org_ghana_fintrust",
    status: "healthy",
    region: "Africa West",
    isolationModel: "dedicated",
    databaseName: "ic_fintrust_prod",
    databaseStatus: "Healthy",
    storageBucket: "identitycore-evidence-fintrust-prod",
    storageUsedGb: 184,
    storageLimitGb: 500,
    apiLatencyMs: 91,
    uptime: "99.99%",
    activeUsers: 248,
    verificationsToday: 6421,
    createdAt: "2026-02-12",
    lastHealthCheckAt: "2026-07-09 09:04",
    environment: "production",
  },
  {
    id: "tenant_lagospay_prod",
    name: "LagosPay Production",
    slug: "lagospay-production",
    organizationName: "LagosPay",
    organizationId: "org_lagos_pay",
    status: "degraded",
    region: "Africa West",
    isolationModel: "schema",
    databaseName: "ic_afwest_shared",
    databaseStatus: "Degraded",
    storageBucket: "identitycore-evidence-lagospay",
    storageUsedGb: 96,
    storageLimitGb: 250,
    apiLatencyMs: 284,
    uptime: "99.82%",
    activeUsers: 119,
    verificationsToday: 3820,
    createdAt: "2026-03-08",
    lastHealthCheckAt: "2026-07-09 09:02",
    environment: "production",
  },
  {
    id: "tenant_civic_registry_staging",
    name: "Civic Registry Staging",
    slug: "civic-registry-staging",
    organizationName: "Civic Registry Authority",
    organizationId: "org_civic_registry",
    status: "provisioning",
    region: "Africa East",
    isolationModel: "database",
    databaseName: "ic_civic_registry_staging",
    databaseStatus: "Migrating",
    storageBucket: "identitycore-evidence-civic-staging",
    storageUsedGb: 12,
    storageLimitGb: 100,
    apiLatencyMs: 171,
    uptime: "Provisioning",
    activeUsers: 8,
    verificationsToday: 0,
    createdAt: "2026-07-01",
    lastHealthCheckAt: "2026-07-09 08:58",
    environment: "staging",
  },
  {
    id: "tenant_eduverify_prod",
    name: "EduVerify Production",
    slug: "eduverify-production",
    organizationName: "EduVerify Africa",
    organizationId: "org_eduverify",
    status: "healthy",
    region: "Africa West",
    isolationModel: "shared",
    databaseName: "ic_afwest_shared",
    databaseStatus: "Healthy",
    storageBucket: "identitycore-evidence-eduverify",
    storageUsedGb: 42,
    storageLimitGb: 100,
    apiLatencyMs: 122,
    uptime: "99.94%",
    activeUsers: 41,
    verificationsToday: 871,
    createdAt: "2026-04-19",
    lastHealthCheckAt: "2026-07-09 09:01",
    environment: "production",
  },
  {
    id: "tenant_healthpass_prod",
    name: "HealthPass Production",
    slug: "healthpass-production",
    organizationName: "HealthPass Clinics",
    organizationId: "org_healthpass",
    status: "maintenance",
    region: "Africa South",
    isolationModel: "database",
    databaseName: "ic_healthpass_prod",
    databaseStatus: "Migrating",
    storageBucket: "identitycore-evidence-healthpass",
    storageUsedGb: 73,
    storageLimitGb: 250,
    apiLatencyMs: 0,
    uptime: "Maintenance",
    activeUsers: 0,
    verificationsToday: 0,
    createdAt: "2026-01-27",
    lastHealthCheckAt: "2026-07-09 08:45",
    environment: "production",
  },
  {
    id: "tenant_borderless_prod",
    name: "Borderless Jobs Production",
    slug: "borderless-jobs-production",
    organizationName: "Borderless Jobs",
    organizationId: "org_borderless_jobs",
    status: "healthy",
    region: "Europe West",
    isolationModel: "dedicated",
    databaseName: "ic_borderless_prod",
    databaseStatus: "Healthy",
    storageBucket: "identitycore-evidence-borderless-prod",
    storageUsedGb: 204,
    storageLimitGb: 600,
    apiLatencyMs: 104,
    uptime: "99.97%",
    activeUsers: 302,
    verificationsToday: 2841,
    createdAt: "2026-05-15",
    lastHealthCheckAt: "2026-07-09 08:59",
    environment: "production",
  },
];

export const tenantHealthEvents = [
  {
    title: "Webhook delivery latency elevated",
    severity: "Warning",
    time: "12 minutes ago",
    description: "Retries increased for organization webhooks in Africa West.",
  },
  {
    title: "Storage lifecycle policy checked",
    severity: "Info",
    time: "1 hour ago",
    description: "Evidence retention and expiry rules completed successfully.",
  },
  {
    title: "Database backup completed",
    severity: "Success",
    time: "3 hours ago",
    description: "Encrypted tenant backup was created and verified.",
  },
];

export const tenantDatabaseReplicas = [
  {
    name: "Primary",
    region: "Africa West",
    status: "Healthy",
    replicationLag: "0ms",
  },
  {
    name: "Read replica",
    region: "Europe West",
    status: "Healthy",
    replicationLag: "41ms",
  },
  {
    name: "Disaster recovery",
    region: "US East",
    status: "Healthy",
    replicationLag: "1.8s",
  },
];

export const tenantIsolationControls = [
  {
    label: "Data boundary",
    value: "Organization-scoped evidence and verification records",
  },
  {
    label: "Encryption",
    value: "Tenant-specific envelope encryption keys",
  },
  {
    label: "Access policy",
    value: "Platform admin access requires audited break-glass approval",
  },
  {
    label: "Network",
    value: "Private service connectivity with restricted ingress",
  },
];

export function getTenantById(tenantId: string) {
  return tenants.find((tenant) => tenant.id === tenantId);
}
