import { backend } from "./backend";

export type Policy = { id: string; name: string; description: string; version: number; status: string; required_document_types: string[]; required_liveness_level: string; face_match_threshold: number; manual_review_threshold: number; verification_expiry_minutes: number; media_retention_days: number; metadata_retention_days: number; updated_at: string };
export type VerificationSummary = { id: string; status: string; purpose: string; external_reference: string; subject: { id: string; full_name: string; email: string }; policy: { id: string; name: string; version: number | null }; created_at: string };
export type VerificationDetail = VerificationSummary & { checks: Record<string, { status: string; score?: number | null }>; decision: { decision: string; reason_detail: string } | null; evidence_report: { download_url: string; pdf_download_url: string } | null };
export type Page<T> = { results: T[]; pagination: { page: number; page_size: number; total: number; total_pages: number } };

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
  manualReviews: () => backend.rest<Page<{ verification_id: string; status: string; risk_level: string; created_at: string }>>("/verifications/manual-reviews"),
  decideReview: (id: string, decision: string, reason_detail: string) => backend.rest(`/verifications/manual-reviews/${id}/decision`, { method: "POST", body: JSON.stringify({ decision, reason_code: "dashboard_manual_review", reason_detail }) }),
};
