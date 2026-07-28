import { NextResponse } from "next/server";
import {
  SESSION_COOKIE,
  SESSION_ID_COOKIE,
  apiUrl,
  requestIsSameOrigin,
  sessionCookieOptions,
} from "@/lib/bff-session";

export async function POST(request: Request) {
  if (!requestIsSameOrigin(request)) {
    return NextResponse.json({ error: "Cross-origin session exchange denied." }, { status: 403 });
  }
  const body = (await request.json().catch(() => null)) as
    | { sessionId?: string; sessionToken?: string }
    | null;
  if (!body?.sessionId || !body.sessionToken || body.sessionToken.length > 4096) {
    return NextResponse.json({ error: "Invalid verification credential." }, { status: 400 });
  }
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 10_000);
  let upstream: Response;
  try {
    upstream = await fetch(apiUrl(`sessions/${encodeURIComponent(body.sessionId)}`), {
      headers: {
        Accept: "application/json",
        Authorization: `Bearer ${body.sessionToken}`,
        "X-Session-Id": body.sessionId,
        "Accept-Language": request.headers.get("accept-language") ?? "en",
      },
      cache: "no-store",
      signal: controller.signal,
    });
  } catch {
    return NextResponse.json({ error: "Verification service unavailable." }, { status: 502 });
  } finally {
    clearTimeout(timeout);
  }
  if (!upstream.ok) {
    return NextResponse.json({ error: "Invalid or expired verification credential." }, { status: 401 });
  }
  const response = NextResponse.json({ success: true });
  response.cookies.set(SESSION_COOKIE, body.sessionToken, sessionCookieOptions);
  response.cookies.set(SESSION_ID_COOKIE, body.sessionId, sessionCookieOptions);
  return response;
}

export async function DELETE(request: Request) {
  if (!requestIsSameOrigin(request)) {
    return NextResponse.json({ error: "Cross-origin request denied." }, { status: 403 });
  }
  const response = NextResponse.json({ success: true });
  response.cookies.set(SESSION_COOKIE, "", { ...sessionCookieOptions, maxAge: 0 });
  response.cookies.set(SESSION_ID_COOKIE, "", { ...sessionCookieOptions, maxAge: 0 });
  return response;
}
