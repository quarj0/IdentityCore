"use client";

export const DEFAULT_BACKEND_ORIGIN = "http://localhost:8000";

export function getBackendOrigin() {
  const configured = process.env.NEXT_PUBLIC_API_ORIGIN?.trim();
  if (!configured && process.env.NODE_ENV === "production") {
    throw new Error("NEXT_PUBLIC_API_ORIGIN must be configured in production.");
  }
  const origin = configured || DEFAULT_BACKEND_ORIGIN;
  let parsed: URL;
  try {
    parsed = new URL(origin);
  } catch {
    throw new Error("NEXT_PUBLIC_API_ORIGIN must be an absolute HTTP(S) URL.");
  }
  if (!["http:", "https:"].includes(parsed.protocol)) {
    throw new Error("NEXT_PUBLIC_API_ORIGIN must use HTTP or HTTPS.");
  }
  if (process.env.NODE_ENV === "production" && parsed.protocol !== "https:") {
    throw new Error("NEXT_PUBLIC_API_ORIGIN must use HTTPS in production.");
  }
  return parsed.origin;
}

export function getRestApiBaseUrl() {
  return `${getBackendOrigin().replace(/\/$/, "")}/api/v1`;
}

export function getGraphqlApiUrl() {
  return `${getBackendOrigin().replace(/\/$/, "")}/api/graphql`;
}
