"use client";

const API_ORIGIN = process.env.NEXT_PUBLIC_API_ORIGIN ?? "http://localhost:8000";
const API_BASE = `${API_ORIGIN.replace(/\/$/, "")}/api/v1`;
const TOKEN_KEY_PREFIX = "identitycore.verification.";

export interface SessionCredentials {
  sessionId: string;
  sessionToken: string;
}

export interface VerificationSession {
  session_id: string;
  verification_id: string;
  status: string;
  organization: { name: string; logo_url: string };
  purpose: string;
  required_steps: string[];
  document: {
    country_code: string;
    document_type: string;
    label: string;
  };
  expires_at: string;
}

export interface VerificationStatus {
  verification_id: string;
  status: string;
  current_step: string;
  message: string;
  evidence: {
    identity_document_id: string;
    selfie_capture_id: string;
    liveness_check_id: string;
  };
}

interface ApiEnvelope<T> {
  success: boolean;
  data?: T;
  error?: { code?: string; message?: string };
}

async function request<T>(
  credentials: SessionCredentials,
  path: string,
  init: RequestInit = {},
) {
  const headers = new Headers(init.headers);
  headers.set("Accept", "application/json");
  headers.set("Authorization", `Bearer ${credentials.sessionToken}`);
  headers.set("X-Session-Id", credentials.sessionId);
  if (init.body && !(init.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  const response = await fetch(`${API_BASE}${path}`, { ...init, headers });
  const body = await response.text();
  let payload: ApiEnvelope<T>;
  try {
    payload = JSON.parse(body) as ApiEnvelope<T>;
  } catch {
    throw new Error("The verification service is temporarily unavailable. Please try again shortly.");
  }
  if (!response.ok || !payload.success || !payload.data) {
    const message = payload.error?.message ?? "Verification request failed. Please try again.";
    throw new Error(
      /unexpected token|invalidtag|not valid json|json\.parse|syntaxerror/i.test(message)
        ? "The verification service is temporarily unavailable. Please try again shortly."
        : message,
    );
  }
  return payload.data;
}

export function consumeSessionCredentials(sessionId: string) {
  const hash = new URLSearchParams(window.location.hash.replace(/^#/, ""));
  const fragmentToken = hash.get("token");
  const storageKey = `${TOKEN_KEY_PREFIX}${sessionId}`;
  if (fragmentToken) {
    window.sessionStorage.setItem(storageKey, fragmentToken);
    window.history.replaceState(null, "", window.location.pathname);
  }
  const sessionToken = fragmentToken ?? window.sessionStorage.getItem(storageKey);
  return sessionToken ? { sessionId, sessionToken } : null;
}

export function clearSessionCredentials(sessionId: string) {
  window.sessionStorage.removeItem(`${TOKEN_KEY_PREFIX}${sessionId}`);
}

export function fetchVerificationSession(credentials: SessionCredentials) {
  return request<VerificationSession>(credentials, `/sessions/${credentials.sessionId}`);
}

export function fetchVerificationStatus(credentials: SessionCredentials) {
  return request<VerificationStatus>(
    credentials,
    `/sessions/${credentials.sessionId}/status`,
  );
}

export function acceptConsent(credentials: SessionCredentials) {
  return request(credentials, `/sessions/${credentials.sessionId}/consent`, {
    method: "POST",
    body: JSON.stringify({ accepted: true }),
  });
}

export async function createUpload(
  credentials: SessionCredentials,
  purpose: "document_capture" | "selfie_capture",
  file: File,
) {
  const upload = await request<{
    upload_id: string;
    upload_url: string;
    upload_headers: Record<string, string>;
    upload_transfer_path: string;
  }>(
    credentials,
    "/uploads/",
    {
      method: "POST",
      body: JSON.stringify({
        purpose,
        mime_type: file.type,
        file_size_bytes: file.size,
      }),
    },
  );
  const form = new FormData();
  form.set("file", file);
  await request(credentials, upload.upload_transfer_path, {
    method: "POST",
    body: form,
  });
  return upload.upload_id;
}

export function submitDocument(
  credentials: SessionCredentials,
  input: { documentType: string; countryCode: string; uploadId: string },
) {
  return request(credentials, `/sessions/${credentials.sessionId}/documents`, {
    method: "POST",
    body: JSON.stringify({
      document_type: input.documentType,
      country_code: input.countryCode,
      captures: [{ side: "front", upload_id: input.uploadId }],
    }),
  });
}

export function submitSelfie(credentials: SessionCredentials, uploadId: string) {
  return request<{ selfie_capture_id: string }>(
    credentials,
    `/sessions/${credentials.sessionId}/selfies`,
    {
      method: "POST",
      body: JSON.stringify({ capture_type: "image", upload_id: uploadId }),
    },
  );
}

export function submitLiveness(
  credentials: SessionCredentials,
  selfieCaptureId: string,
) {
  return request(credentials, `/sessions/${credentials.sessionId}/liveness`, {
    method: "POST",
    body: JSON.stringify({
      liveness_type: "passive",
      selfie_capture_id: selfieCaptureId,
    }),
  });
}
