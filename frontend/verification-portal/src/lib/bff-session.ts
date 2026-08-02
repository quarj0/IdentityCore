import { cookies } from "next/headers";
import { randomUUID } from "node:crypto";

const production = process.env.NODE_ENV === "production";
export const SESSION_COOKIE = `${production ? "__Host-" : ""}identitycore_verify`;
export const SESSION_ID_COOKIE = `${production ? "__Host-" : ""}identitycore_verify_id`;

export const sessionCookieOptions = {
  httpOnly: true,
  secure: production,
  sameSite: "strict" as const,
  path: "/",
};

export async function readBffSession() {
  const store = await cookies();
  const sessionToken = store.get(SESSION_COOKIE)?.value;
  const sessionId = store.get(SESSION_ID_COOKIE)?.value;
  return sessionToken && sessionId ? { sessionToken, sessionId } : null;
}

export function runtimeConfiguration() {
  const configuredOrigin = process.env.API_ORIGIN;
  const errors: string[] = [];

  if (production && !process.env.API_ORIGIN) {
    errors.push("API_ORIGIN is required in production.");
  }
  if (!configuredOrigin) {
    return {
      apiOrigin: production ? "" : "http://localhost:8000",
      errors,
    };
  }

  try {
    const url = new URL(configuredOrigin);
    if (!["http:", "https:"].includes(url.protocol)) {
      errors.push("API_ORIGIN must use HTTP or HTTPS.");
    }
    if (production && url.protocol !== "https:") {
      errors.push("API_ORIGIN must use HTTPS in production.");
    }
    if (
      url.username ||
      url.password ||
      url.pathname !== "/" ||
      url.search ||
      url.hash
    ) {
      errors.push(
        "API_ORIGIN must be an origin without credentials, a path, a query, or a fragment.",
      );
    }
    return { apiOrigin: url.origin, errors };
  } catch {
    errors.push("API_ORIGIN is not a valid URL origin.");
    return { apiOrigin: "", errors };
  }
}

export function apiUrl(path: string) {
  const configuration = runtimeConfiguration();
  if (configuration.errors.length || !configuration.apiOrigin) {
    throw new Error(configuration.errors.join(" ") || "API_ORIGIN is invalid.");
  }
  return `${configuration.apiOrigin}/api/v1/${path.replace(/^\//, "")}`;
}

export function requestId(request: Request) {
  const incoming = request.headers.get("x-request-id")?.trim();
  return incoming && /^[A-Za-z0-9._-]{1,128}$/.test(incoming)
    ? incoming
    : randomUUID();
}

export function responseHeaders(id: string, contentType = "application/json") {
  return {
    "Cache-Control": "no-store",
    "Content-Type": contentType,
    "X-Request-Id": id,
  };
}

export function requestIsSameOrigin(request: Request) {
  if (request.headers.get("sec-fetch-site") === "cross-site") return false;
  const origin = request.headers.get("origin");
  if (!origin) return true;
  return origin === new URL(request.url).origin;
}
