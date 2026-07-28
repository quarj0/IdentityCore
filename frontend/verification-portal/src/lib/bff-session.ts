import { cookies } from "next/headers";

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

export function apiUrl(path: string) {
  const origin = process.env.API_ORIGIN ?? process.env.NEXT_PUBLIC_API_ORIGIN ?? "http://localhost:8000";
  return `${origin.replace(/\/$/, "")}/api/v1/${path.replace(/^\//, "")}`;
}

export function requestIsSameOrigin(request: Request) {
  if (request.headers.get("sec-fetch-site") === "cross-site") return false;
  const origin = request.headers.get("origin");
  if (!origin) return true;
  return origin === new URL(request.url).origin;
}
