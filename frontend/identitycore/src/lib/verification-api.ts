"use client";

import { restRequest } from "@/lib/api-client";

export interface VerificationCreateResponse {
  id: string;
  status: string;
  verification_url: string;
  session_id: string;
  session_token: string;
  expires_at: string;
}

export interface VerificationSessionSummary {
  session_id: string;
  verification_id: string;
  status: string;
  organization: {
    name: string;
    logo_url: string;
  };
  purpose: string;
  required_steps: string[];
  expires_at: string;
}

export interface VerificationStatusResponse {
  verification_id: string;
  status: string;
  current_step: string;
  message: string;
}

export interface VerificationDetailResponse {
  id: string;
  status: string;
  purpose: string;
  external_reference: string;
  verification_subject: {
    id: string;
    full_name: string;
  };
  checks: {
    document: { status: string };
    liveness: { status: string; score: number | null };
    face_match: { status: string; score: number | null };
  };
  decision: {
    decision: string;
    decision_type: string;
    reason_code: string;
    reason_detail: string;
    decided_at: string;
  } | null;
  evidence_report: {
    storage_key: string;
    download_url: string;
    pdf_storage_key: string;
    pdf_download_url: string;
  } | null;
  created_at: string;
  completed_at: string | null;
  expires_at: string;
}

interface UploadCreateResponse {
  upload_id: string;
  upload_url: string;
  expires_at: string;
}

export interface SessionCredentials {
  sessionId: string;
  sessionToken: string;
}

function buildSessionHeaders(credentials: SessionCredentials) {
  return {
    Authorization: `Bearer ${credentials.sessionToken}`,
    "X-Session-Id": credentials.sessionId,
  };
}

export async function createAdminOnboardingVerification(input: {
  fullName: string;
  email: string;
}) {
  return restRequest<VerificationCreateResponse>("/verifications/", {
    method: "POST",
    body: JSON.stringify({
      purpose: "Administrator identity onboarding",
      verification_subject: {
        full_name: input.fullName,
        email: input.email,
      },
      metadata: {
        source: "identitycore_onboarding",
      },
    }),
  });
}

export async function fetchVerificationSession(credentials: SessionCredentials) {
  return restRequest<VerificationSessionSummary>(
    `/sessions/${credentials.sessionId}`,
    {
      headers: buildSessionHeaders(credentials),
    },
    { token: null, useAuth: false },
  );
}

export async function acceptVerificationConsent(
  credentials: SessionCredentials,
  accepted: boolean,
) {
  return restRequest<{ consent_record_id: string; next_step: string }>(
    `/sessions/${credentials.sessionId}/consent`,
    {
      method: "POST",
      headers: buildSessionHeaders(credentials),
      body: JSON.stringify({ accepted }),
    },
    { token: null, useAuth: false },
  );
}

export async function createSessionUpload(
  credentials: SessionCredentials,
  purpose: "document_capture" | "selfie_capture" | "liveness_capture",
  file: File,
) {
  const upload = await restRequest<UploadCreateResponse>(
    "/uploads/",
    {
      method: "POST",
      headers: buildSessionHeaders(credentials),
      body: JSON.stringify({
        purpose,
        mime_type: file.type,
        file_size_bytes: file.size,
      }),
    },
    { token: null, useAuth: false },
  );

  const uploadResponse = await fetch(upload.upload_url, {
    method: "PUT",
    headers: {
      "Content-Type": file.type,
    },
    body: file,
  });

  if (!uploadResponse.ok) {
    throw new Error("Upload transfer failed.");
  }

  return upload;
}

export async function submitVerificationDocument(
  credentials: SessionCredentials,
  input: {
    documentType: string;
    countryCode?: string;
    captures: Array<{ side: string; upload_id: string }>;
  },
) {
  return restRequest<{
    identity_document_id: string;
    status: string;
    next_step: string;
  }>(
    `/sessions/${credentials.sessionId}/documents`,
    {
      method: "POST",
      headers: buildSessionHeaders(credentials),
      body: JSON.stringify({
        document_type: input.documentType,
        country_code: input.countryCode ?? "",
        captures: input.captures,
      }),
    },
    { token: null, useAuth: false },
  );
}

export async function submitVerificationSelfie(
  credentials: SessionCredentials,
  input: {
    captureType: "image" | "video";
    uploadId: string;
  },
) {
  return restRequest<{
    selfie_capture_id: string;
    status: string;
    next_step: string;
  }>(
    `/sessions/${credentials.sessionId}/selfies`,
    {
      method: "POST",
      headers: buildSessionHeaders(credentials),
      body: JSON.stringify({
        capture_type: input.captureType,
        upload_id: input.uploadId,
      }),
    },
    { token: null, useAuth: false },
  );
}

export async function submitVerificationLiveness(
  credentials: SessionCredentials,
  input: {
    livenessType: "passive" | "active";
    selfieCaptureId: string;
  },
) {
  return restRequest<{
    liveness_check_id: string;
    status: string;
  }>(
    `/sessions/${credentials.sessionId}/liveness`,
    {
      method: "POST",
      headers: buildSessionHeaders(credentials),
      body: JSON.stringify({
        liveness_type: input.livenessType,
        selfie_capture_id: input.selfieCaptureId,
      }),
    },
    { token: null, useAuth: false },
  );
}

export async function fetchVerificationStatus(credentials: SessionCredentials) {
  return restRequest<VerificationStatusResponse>(
    `/sessions/${credentials.sessionId}/status`,
    {
      headers: buildSessionHeaders(credentials),
    },
    { token: null, useAuth: false },
  );
}

export async function fetchVerificationDetail(verificationId: string) {
  return restRequest<VerificationDetailResponse>(`/verifications/${verificationId}`);
}
