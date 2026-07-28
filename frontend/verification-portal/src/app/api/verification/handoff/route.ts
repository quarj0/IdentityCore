import { NextResponse } from "next/server";
import {
  apiUrl,
  requestIsSameOrigin,
  SESSION_COOKIE,
  SESSION_ID_COOKIE,
  sessionCookieOptions,
} from "@/lib/bff-session";

export async function POST(request: Request) {
  if (!requestIsSameOrigin(request)) {
    return NextResponse.json(
      { error: "Cross-origin handoff denied." },
      { status: 403 },
    );
  }
  const upstream = await fetch(apiUrl("sessions/mobile-handoff/redeem"), {
    method: "POST",
    headers: { Accept: "application/json", "Content-Type": "application/json" },
    body: await request.text(),
    cache: "no-store",
  });
  const text = await upstream.text();
  const payload = JSON.parse(text) as {
    data?: { session_id?: string; session_token?: string };
  };
  if (upstream.ok && payload.data?.session_id && payload.data.session_token) {
    const token = payload.data.session_token;
    delete payload.data.session_token;
    const sanitized = NextResponse.json(payload, { status: upstream.status });
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
    headers: {
      "Content-Type":
        upstream.headers.get("content-type") ?? "application/json",
    },
  });
}
