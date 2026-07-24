"use client";

import { createIdentityCoreClient } from "@identitycore/api-client";

let accessToken: string | null = null;

export const backend = createIdentityCoreClient({
  apiOrigin: process.env.NEXT_PUBLIC_API_ORIGIN ?? "http://localhost:8000",
  getAccessToken: () => accessToken,
  setAccessToken: (token) => { accessToken = token; },
  sessionScope: "dashboard",
});
