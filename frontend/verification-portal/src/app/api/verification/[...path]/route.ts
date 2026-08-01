import { NextResponse } from "next/server";
import {
  apiUrl,
  readBffSession,
  requestId,
  requestIsSameOrigin,
  responseHeaders,
} from "@/lib/bff-session";

const MAX_PROXY_BODY_BYTES = 26 * 1024 * 1024;
const SAFE_SEGMENT = /^[A-Za-z0-9_-]{1,128}$/;

function pathIsAllowed(path: string[]) {
  if (!path.length || path.some((segment) => !SAFE_SEGMENT.test(segment))) {
    return false;
  }
  if (path[0] === "uploads") {
    return path.length === 1 || (path.length === 3 && path[2] === "transfer");
  }
  if (path[0] !== "sessions" || !path[1] || path.length > 4) return false;
  if (path.length === 2) return true;
  const action = path[2];
  if (
    ["status", "consent", "mobile-handoff", "documents", "selfies"].includes(
      action,
    )
  ) {
    return path.length === 3;
  }
  return (
    action === "liveness" && (path.length === 3 || path[3] === "challenge")
  );
}

async function proxy(
  request: Request,
  context: { params: Promise<{ path: string[] }> },
) {
  const id = requestId(request);
  const session = await readBffSession();
  if (!session)
    return NextResponse.json(
      { error: { message: "Verification session is not authenticated." } },
      { status: 401, headers: responseHeaders(id) },
    );
  if (request.method !== "GET" && !requestIsSameOrigin(request)) {
    return NextResponse.json(
      { error: { message: "Cross-origin request denied." } },
      { status: 403, headers: responseHeaders(id) },
    );
  }
  const { path } = await context.params;
  if (!pathIsAllowed(path)) {
    return NextResponse.json(
      { error: { message: "Verification route is not allowed." } },
      { status: 404, headers: responseHeaders(id) },
    );
  }
  if (path[0] === "sessions" && path[1] && path[1] !== session.sessionId) {
    return NextResponse.json(
      { error: { message: "Session identifier mismatch." } },
      { status: 403, headers: responseHeaders(id) },
    );
  }
  const declaredLength = Number(request.headers.get("content-length") ?? 0);
  if (declaredLength > MAX_PROXY_BODY_BYTES) {
    return NextResponse.json(
      { error: { message: "Verification request is too large." } },
      { status: 413, headers: responseHeaders(id) },
    );
  }
  const headers = new Headers();
  headers.set("Accept", "application/json");
  headers.set("Authorization", `Bearer ${session.sessionToken}`);
  headers.set("X-Session-Id", session.sessionId);
  headers.set("X-Request-Id", id);
  headers.set(
    "Accept-Language",
    request.headers.get("accept-language") ?? "en",
  );
  const contentType = request.headers.get("content-type");
  if (contentType) headers.set("Content-Type", contentType);
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 30_000);
  let upstream: Response;
  try {
    const query = new URL(request.url).search;
    const body =
      request.method === "GET" || request.method === "HEAD"
        ? undefined
        : await request.arrayBuffer();
    if (body && body.byteLength > MAX_PROXY_BODY_BYTES) {
      return NextResponse.json(
        { error: { message: "Verification request is too large." } },
        { status: 413, headers: responseHeaders(id) },
      );
    }
    upstream = await fetch(`${apiUrl(path.join("/"))}${query}`, {
      method: request.method,
      headers,
      body,
      cache: "no-store",
      redirect: "manual",
      signal: controller.signal,
    });
  } catch {
    return NextResponse.json(
      { error: { message: "Verification service unavailable." } },
      { status: 502, headers: responseHeaders(id) },
    );
  } finally {
    clearTimeout(timeout);
  }
  return new NextResponse(upstream.body, {
    status: upstream.status,
    headers: responseHeaders(
      id,
      upstream.headers.get("content-type") ?? "application/json",
    ),
  });
}

export const GET = proxy;
export const POST = proxy;
export const PUT = proxy;
export const PATCH = proxy;
export const DELETE = proxy;
