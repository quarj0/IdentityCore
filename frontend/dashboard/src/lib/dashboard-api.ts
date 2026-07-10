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
  action: string;
  target_type: string;
  target_id: string;
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
};

export type Tenant = {
  id: string;
  name: string;
  slug: string;
  status: string;
  settings: Record<string, unknown>;
};

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
  notifications: () => backend.rest<{ results: Notification[] }>("/notifications/"),
  team: () => backend.rest<{ results: DashboardUser[] }>("/auth/team"),
  subjects: () => backend.rest<Page<VerificationSubject>>("/subjects/"),
  organization: () => backend.rest<Organization>("/organization/me/"),
  tenant: () => backend.rest<Tenant>("/tenant/me/"),
};
