import { subjectMetadataHeaders } from "@/lib/bff-subject-metadata";
import { NextResponse } from "next/server";
import { ProxyBodyLimitError, readBoundedRequestText } from "@/lib/bff-proxy";
import {
  SESSION_COOKIE,
  SESSION_ID_COOKIE,
  apiUrl,
  requestId,
  requestIsSameOrigin,
  responseHeaders,
  sessionCookieOptions,
} from "@/lib/bff-session";

export async function POST(request: Request) {
  const id = requestId(request);
  if (!requestIsSameOrigin(request)) {
    return NextResponse.json(
      { error: "Cross-origin session exchange denied." },
      { status: 403, headers: responseHeaders(id) },
    );
  }
  let body: { sessionId?: unknown; sessionToken?: unknown } | null;
  try {
    body = JSON.parse(await readBoundedRequestText(request, 8192));
  } catch (error) {
    const status =
      error instanceof ProxyBodyLimitError
        ? 413
        : error instanceof DOMException && error.name === "AbortError"
          ? 408
          : 400;
    return NextResponse.json(
      { error: "Invalid verification request." },
      { status, headers: responseHeaders(id) },
    );
  }
  if (
    typeof body?.sessionId !== "string" ||
    !/^[A-Za-z0-9_-]{1,128}$/.test(body.sessionId) ||
    typeof body.sessionToken !== "string" ||
    !body.sessionToken ||
    !/^[\x21-\x7e]{1,4096}$/.test(body.sessionToken)
  ) {
    return NextResponse.json(
      { error: "Invalid verification credential." },
      { status: 400, headers: responseHeaders(id) },
    );
  }
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 10_000);
  let upstream: Response;
  try {
    const upstreamUrl = apiUrl(
      `sessions/${encodeURIComponent(body.sessionId)}`,
    );
    upstream = await fetch(upstreamUrl, {
      headers: {
        ...subjectMetadataHeaders(
          request,
          upstreamUrl,
          "GET",
          `Bearer ${body.sessionToken}`,
          id,
        ),
        Accept: "application/json",
        Authorization: `Bearer ${body.sessionToken}`,
        "X-Session-Id": body.sessionId,
        "Accept-Language": request.headers.get("accept-language") ?? "en",
        "X-Request-Id": id,
      },
      cache: "no-store",
      redirect: "manual",
      signal: controller.signal,
    });
  } catch {
    return NextResponse.json(
      { error: "Verification service unavailable." },
      { status: 502, headers: responseHeaders(id) },
    );
  } finally {
    clearTimeout(timeout);
  }
  if (!upstream.ok) {
    return NextResponse.json(
      { error: "Invalid or expired verification credential." },
      { status: 401, headers: responseHeaders(id) },
    );
  }
  const response = NextResponse.json(
    { success: true },
    { headers: responseHeaders(id) },
  );
  response.cookies.set(SESSION_COOKIE, body.sessionToken, sessionCookieOptions);
  response.cookies.set(SESSION_ID_COOKIE, body.sessionId, sessionCookieOptions);
  return response;
}

export async function DELETE(request: Request) {
  const id = requestId(request);
  if (!requestIsSameOrigin(request)) {
    return NextResponse.json(
      { error: "Cross-origin request denied." },
      { status: 403, headers: responseHeaders(id) },
    );
  }
  const response = NextResponse.json(
    { success: true },
    { headers: responseHeaders(id) },
  );
  response.cookies.set(SESSION_COOKIE, "", {
    ...sessionCookieOptions,
    maxAge: 0,
  });
  response.cookies.set(SESSION_ID_COOKIE, "", {
    ...sessionCookieOptions,
    maxAge: 0,
  });
  return response;
}
