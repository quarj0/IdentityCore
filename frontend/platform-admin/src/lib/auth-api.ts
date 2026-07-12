"use client";

import { getBackendOrigin } from "@/lib/config";

interface LoginResponse {
  tokens: {
    access: string;
  };
}

export function login(email: string, password: string) {
  return fetch(`${getBackendOrigin().replace(/\/$/, "")}/api/v1/auth/login`, {
    method: "POST",
    credentials: "include",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ email, password }),
  }).then(async (response) => {
    const payload = (await response.json()) as LoginResponse;
    if (!response.ok || !payload.tokens?.access) {
      throw new Error("Unable to sign in. Please check your credentials and try again.");
    }
    return payload;
  });
}
