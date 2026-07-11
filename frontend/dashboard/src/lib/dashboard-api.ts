import { backend } from "./backend";

export type Policy = {
  id: string;
  name: string;
  description: string;
  version: number;
  status: "draft" | "active" | "archived" | string;
  required_document_types: string[];
  required_liveness_level: string;
  face_match_threshold: number;
  manual_review_threshold: number;
  verification_expiry_minutes: number;
  media_retention_days: number;
  metadata_retention_days: number;
  created_at?: string;
  updated_at: string;
};

export type VerificationSummary = {
  id: string;
  status: string;
  purpose: string;
  external_reference: string;
  subject: { id: string; full_name: string; email: string };
  policy: { id: string; name: string; version: number | null };
  created_at: string;
  completed_at?: string | null;
};

export type VerificationDetail = {
  id: string;
  status: string;
  purpose: string;
  external_reference: string;
  verification_subject: {
    id: string;
    full_name: string;
    email?: string;
    phone_number?: string;
  };
  subject?: VerificationSummary["subject"];
  policy: { id: string; name: string; version: number | null };
  checks: Record<string, { status: string; score?: number | null }>;
  risk_assessment: {
    id: string;
    risk_level: string;
    risk_score: number;
    recommendation: string;
  } | null;
  decision: {
    decision: string;
    decision_type: string;
    reason_code: string;
    reason_detail: string;
    decided_at: string;
  } | null;
  evidence_report: { download_url: string; pdf_download_url: string } | null;
  created_at: string;
  completed_at: string | null;
  expires_at: string;
};

export type Page<T> = { results: T[]; pagination: { page: number; page_size: number; total: number; total_pages: number } };

export type ManualReviewSummary = {
  verification_id: string;
  subject: { full_name: string; email?: string };
  purpose: string;
  status: string;
  risk_level: string;
  created_at: string;
};

export type AuditEvent = {
  id: string;
  actor_type: string;
  actor_id: string;
  actor_display_name: string;
  action: string;
  action_label: string;
  target_type: string;
  target_id: string;
  target_label: string;
  ip_address: string;
  user_agent: string;
  metadata: Record<string, unknown>;
  created_at: string;
};

export type WebhookEndpoint = {
  id: string;
  url: string;
  description: string;
  events: string[];
  status: string;
  created_at: string;
  updated_at: string;
};

export type APIClient = {
  public_id: string;
  name: string;
  client_id: string;
  client_secret?: string;
  status: string;
  scopes: string[];
  allowed_networks: string[];
  rate_limit_per_minute: number;
  last_used_at: string | null;
  created_at: string;
  updated_at: string;
};

export type DashboardUser = {
  public_id: string;
  email: string;
  first_name: string;
  last_name: string;
  phone_number: string;
  status: string;
  tenant_public_id: string | null;
  roles: string[];
  mfa_enabled: boolean;
};

export type Notification = {
  id: string;
  recipient_type: string;
  recipient: string;
  channel: string;
  template_code: string;
  status: string;
  subject: string;
  body_preview: string;
  sent_at: string | null;
  created_at: string;
};

export type VerificationSubject = {
  id: string;
  external_reference: string;
  full_name: string;
  email: string;
  phone_number: string;
  date_of_birth: string | null;
  created_at: string;
};

export type Organization = {
  id: string;
  name: string;
  slug: string;
  industry: string;
  status: string;
  settings: Record<string, unknown>;
  sandbox_usage: { pending_approval: boolean; projects: number; project_limit: number | null; api_keys: number; api_key_limit: number | null; workflows: number; workflow_limit: number | null; webhooks: number; webhook_limit: number | null; monthly_verifications: number; monthly_verification_limit: number | null };
};

export type Tenant = {
  id: string;
  name: string;
  slug: string;
  status: string;
  settings: Record<string, unknown>;
};
export type Project = { id: string; name: string; slug: string; environment: "sandbox" | "production"; status: string; allowed_origins: string[]; is_default: boolean; created_at: string; updated_at: string };
export type WorkflowDefinition = { id: string; project_id: string; name: string; description: string; status: string; steps: string[]; settings: Record<string, unknown>; current_version: number; created_at: string; updated_at: string };

export const supportedWebhookEvents = [
  "verification.created",
  "verification.consent_accepted",
  "verification.document_uploaded",
  "verification.selfie_uploaded",
  "verification.processing",
  "verification.manual_review_required",
  "verification.verified",
  "verification.rejected",
  "verification.expired",
  "verification.cancelled",
];

export const dashboardApi = {
  documentTypes: () => backend.rest<Array<{ code: string; name: string }>>("/document-types"),
  policies: () => backend.rest<Policy[]>("/policies/"),
  policy: (id: string) => backend.rest<Policy>(`/policies/${id}`),
  createPolicy: (input: Record<string, unknown>) => backend.rest<Policy>("/policies/", { method: "POST", body: JSON.stringify(input) }),
  patchPolicy: (id: string, input: Record<string, unknown>) => backend.rest<Policy>(`/policies/${id}`, { method: "PATCH", body: JSON.stringify(input) }),
  policyAction: (id: string, action: "clone" | "activate" | "archive") => backend.rest<Policy>(`/policies/${id}/${action}`, { method: "POST" }),
  verifications: (status = "") => backend.rest<Page<VerificationSummary>>(`/verifications/${status ? `?status=${encodeURIComponent(status)}` : ""}`),
  verification: (id: string) => backend.rest<VerificationDetail>(`/verifications/${id}`),
  createVerification: (input: Record<string, unknown>) => backend.rest<{ id: string; status: string; verification_url: string; expires_at: string }>("/verifications/", { method: "POST", body: JSON.stringify(input) }),
  cancelVerification: (id: string, reason: string) => backend.rest(`/verifications/${id}/cancel`, { method: "POST", body: JSON.stringify({ reason }) }),
  resendVerification: (id: string) => backend.rest<{ verification_url: string; expires_at: string }>(`/verifications/${id}/resend-link`, { method: "POST", body: JSON.stringify({ channel: "email" }) }),
  manualReviews: () => backend.rest<Page<ManualReviewSummary>>("/verifications/manual-reviews"),
  decideReview: (id: string, decision: string, reason_detail: string) => backend.rest(`/verifications/manual-reviews/${id}/decision`, { method: "POST", body: JSON.stringify({ decision, reason_code: "dashboard_manual_review", reason_detail }) }),
  auditEvents: () => backend.rest<Page<AuditEvent>>("/audit-events/"),
  webhooks: () => backend.rest<{ results: WebhookEndpoint[] }>("/webhook-endpoints/"),
  createWebhook: (input: Record<string, unknown>) => backend.rest<{ id: string; secret: string; status: string }>("/webhook-endpoints/", { method: "POST", body: JSON.stringify(input) }),
  testWebhook: (id: string) => backend.rest<{ queued: boolean }>(`/webhook-endpoints/${id}/test`, { method: "POST", body: JSON.stringify({}) }),
  apiClients: () => backend.rest<{ results: APIClient[] }>("/api-clients/"),
  createApiClient: (input: Record<string, unknown>) => backend.rest<APIClient>("/api-clients/", { method: "POST", body: JSON.stringify(input) }),
  apiClientAction: (id: string, action: "rotate" | "revoke") => backend.rest<APIClient>(`/api-clients/${id}/${action}`, { method: "POST", body: "{}" }),
  notifications: () => backend.rest<{ results: Notification[] }>("/notifications/"),
  team: () => backend.rest<{ results: DashboardUser[] }>("/auth/team"),
  subjects: () => backend.rest<Page<VerificationSubject>>("/subjects/"),
  organization: () => backend.rest<Organization>("/organization/me/"),
  updateBranding: (input: { logo_storage_key: string }) => backend.rest<Organization>("/organization/me/", { method: "PATCH", body: JSON.stringify(input) }),
  createBrandingUpload: (input: { asset_type: "logo" | "branding_image"; filename: string; mime_type: string }) => backend.rest<{ storage_key: string; upload_url: string; asset_url: string }>("/organization/me/branding/assets/upload/", { method: "POST", body: JSON.stringify(input) }),
  tenant: () => backend.rest<Tenant>("/tenant/me/"),
  projects: () => backend.rest<{ results: Project[] }>("/projects/"),
  project: (id: string) => backend.rest<Project>(`/projects/${id}`),
  createProject: (input: Record<string, unknown>) => backend.rest<Project>("/projects/", { method: "POST", body: JSON.stringify(input) }),
  patchProject: (id: string, input: Record<string, unknown>) => backend.rest<Project>(`/projects/${id}`, { method: "PATCH", body: JSON.stringify(input) }),
  projectAction: (id: string, action: "suspend" | "reactivate") => backend.rest<Project>(`/projects/${id}/${action}`, { method: "POST", body: "{}" }),
  workflows: (projectId = "") => backend.rest<{ results: WorkflowDefinition[] }>(`/workflows/${projectId ? `?project_id=${encodeURIComponent(projectId)}` : ""}`),
  workflow: (id: string) => backend.rest<WorkflowDefinition>(`/workflows/${id}`),
  createWorkflow: (input: Record<string, unknown>) => backend.rest<WorkflowDefinition>("/workflows/", { method: "POST", body: JSON.stringify(input) }),
  patchWorkflow: (id: string, input: Record<string, unknown>) => backend.rest<WorkflowDefinition>(`/workflows/${id}`, { method: "PATCH", body: JSON.stringify(input) }),
  workflowAction: (id: string, action: "clone" | "publish" | "archive") => backend.rest<WorkflowDefinition>(`/workflows/${id}/${action}`, { method: "POST", body: "{}" }),
  workflowVersions: (id: string) => backend.rest<{ results: Array<Record<string, unknown>> }>(`/workflows/${id}/versions`),
  subject: (id: string) => backend.rest<Record<string, unknown>>(`/subjects/${id}`),
  auditEvent: (id: string) => backend.rest<Record<string, unknown>>(`/audit-events/${id}`),
  webhook: (id: string) => backend.rest<Record<string, unknown>>(`/webhook-endpoints/${id}`),
  profile: () => backend.me<DashboardUser>(),
  updateProfile: (input: Record<string, unknown>) => backend.rest<{ user: DashboardUser }>("/auth/me", { method: "PATCH", body: JSON.stringify(input) }),
  notificationPreferences: () => backend.rest<{ preferences: Record<string, boolean> }>("/auth/notification-preferences"),
  updateNotificationPreferences: (input: Record<string, boolean>) => backend.rest<{ preferences: Record<string, boolean> }>("/auth/notification-preferences", { method: "PATCH", body: JSON.stringify(input) }),
  invitations: () => backend.rest<{ results: Array<Record<string, unknown>> }>("/auth/team/invitations"),
  createInvitation: (input: Record<string, unknown>) => backend.rest<Record<string, unknown>>("/auth/team/invitations", { method: "POST", body: JSON.stringify(input) }),
  roles: () => backend.rest<{ results: Array<{ id: string; name: string }> }>("/access-control/roles/"),
  suspendWorkspace: (confirmation: string) => backend.rest<{ suspended: boolean }>("/organization/me/suspend", { method: "POST", body: JSON.stringify({ confirmation }) }),
};
