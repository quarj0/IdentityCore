"use client";

export const DEFAULT_BACKEND_ORIGIN = "http://localhost:8000";

export function getBackendOrigin() {
  return process.env.NEXT_PUBLIC_API_ORIGIN ?? DEFAULT_BACKEND_ORIGIN;
}

export function getRestApiBaseUrl() {
  return `${getBackendOrigin().replace(/\/$/, "")}/api/v1`;
}

export function getGraphqlApiUrl() {
  return `${getBackendOrigin().replace(/\/$/, "")}/api/graphql`;
}
