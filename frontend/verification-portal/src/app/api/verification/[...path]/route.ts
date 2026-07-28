import { NextResponse } from "next/server";
import { apiUrl, readBffSession, requestIsSameOrigin } from "@/lib/bff-session";

async function proxy(
  request: Request,
  context: { params: Promise<{ path: string[] }> },
) {
  const session = await readBffSession();
  if (!session)
    return NextResponse.json(
      { error: { message: "Verification session is not authenticated." } },
      { status: 401 },
    );
  if (request.method !== "GET" && !requestIsSameOrigin(request)) {
    return NextResponse.json(
      { error: { message: "Cross-origin request denied." } },
      { status: 403 },
    );
  }
  const { path } = await context.params;
  if (path[0] === "sessions" && path[1] && path[1] !== session.sessionId) {
    return NextResponse.json(
      { error: { message: "Session identifier mismatch." } },
      { status: 403 },
    );
  }
  const headers = new Headers();
  headers.set("Accept", "application/json");
  headers.set("Authorization", `Bearer ${session.sessionToken}`);
  headers.set("X-Session-Id", session.sessionId);
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
    upstream = await fetch(`${apiUrl(path.join("/"))}${query}`, {
      method: request.method,
      headers,
      body:
        request.method === "GET" || request.method === "HEAD"
          ? undefined
          : await request.arrayBuffer(),
      cache: "no-store",
      redirect: "manual",
      signal: controller.signal,
    });
  } catch {
    return NextResponse.json(
      { error: { message: "Verification service unavailable." } },
      { status: 502 },
    );
  } finally {
    clearTimeout(timeout);
  }
  return new NextResponse(upstream.body, {
    status: upstream.status,
    headers: {
      "Content-Type":
        upstream.headers.get("content-type") ?? "application/json",
      "Cache-Control": "no-store",
    },
  });
}

export const GET = proxy;
export const POST = proxy;
export const PUT = proxy;
export const PATCH = proxy;
export const DELETE = proxy;
