"use client";

import { getBackendOrigin } from "@/lib/config";

interface ApiEnvelope<T> {
  success: boolean;
  data?: T;
  error?: {
    message?: string;
  };
}

interface LoginResponse {
  tokens: {
    access: string;
    refresh?: string;
  };
}

export async function login(email: string, password: string) {
  const response = await fetch(`${getBackendOrigin().replace(/\/$/, "")}/api/v1/auth/login`, {
    method: "POST",
    credentials: "include",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ email, password }),
  });

  const payload = (await response.json()) as ApiEnvelope<LoginResponse>;
  const access = payload.success ? payload.data?.tokens?.access : "";
  if (!response.ok || !payload.success || !access) {
    throw new Error(
      payload.error?.message ?? "Unable to sign in. Please check your credentials and try again.",
    );
  }

  return payload.data as LoginResponse;
}
