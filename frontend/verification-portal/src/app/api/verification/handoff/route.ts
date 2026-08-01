import { NextResponse } from "next/server";
import {
  apiUrl,
  requestId,
  requestIsSameOrigin,
  responseHeaders,
  SESSION_COOKIE,
  SESSION_ID_COOKIE,
  sessionCookieOptions,
} from "@/lib/bff-session";

export async function POST(request: Request) {
  const id = requestId(request);
  if (!requestIsSameOrigin(request)) {
    return NextResponse.json(
      { error: "Cross-origin handoff denied." },
      { status: 403, headers: responseHeaders(id) },
    );
  }
  const body = await request.text();
  if (body.length > 8192) {
    return NextResponse.json(
      { error: { message: "Mobile handoff request is too large." } },
      { status: 413, headers: responseHeaders(id) },
    );
  }
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 10_000);
  let upstream: Response;
  try {
    upstream = await fetch(apiUrl("sessions/mobile-handoff/redeem"), {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
        "X-Request-Id": id,
      },
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
  const text = await upstream.text();
  let payload: {
    data?: { session_id?: string; session_token?: string };
  };
  try {
    payload = JSON.parse(text) as typeof payload;
  } catch {
    return NextResponse.json(
      {
        error: {
          message: "Verification service returned an invalid response.",
        },
      },
      { status: 502, headers: responseHeaders(id) },
    );
  }
  if (upstream.ok && payload.data?.session_id && payload.data.session_token) {
    const token = payload.data.session_token;
    delete payload.data.session_token;
    const sanitized = NextResponse.json(payload, {
      status: upstream.status,
      headers: responseHeaders(id),
    });
    sanitized.cookies.set(SESSION_COOKIE, token, sessionCookieOptions);
    sanitized.cookies.set(
      SESSION_ID_COOKIE,
      payload.data.session_id,
      sessionCookieOptions,
    );
    return sanitized;
  }
  return new NextResponse(text, {
    status: upstream.status,
    headers: responseHeaders(
      id,
      upstream.headers.get("content-type") ?? "application/json",
    ),
  });
}
