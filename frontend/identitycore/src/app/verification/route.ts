import { NextRequest, NextResponse } from "next/server";

function getVerificationPortalOrigin() {
  const configured = (
    process.env.NEXT_PUBLIC_VERIFICATION_URL ?? "http://localhost:3002"
  ).trim();
  const url = new URL(configured);

  if (!["http:", "https:"].includes(url.protocol)) {
    throw new Error(
      "NEXT_PUBLIC_VERIFICATION_URL must be an absolute HTTP(S) URL.",
    );
  }
  if (process.env.NODE_ENV === "production" && url.protocol !== "https:") {
    throw new Error("NEXT_PUBLIC_VERIFICATION_URL must use HTTPS in production.");
  }

  return url.origin;
}

export function GET(request: NextRequest) {
  const sessionId =
    request.nextUrl.searchParams.get("sessionId") ??
    request.nextUrl.searchParams.get("session_id");
  const portalOrigin = getVerificationPortalOrigin();

  if (!sessionId) {
    return NextResponse.redirect(portalOrigin);
  }

  const verificationId =
    request.nextUrl.searchParams.get("verificationId") ??
    request.nextUrl.searchParams.get("verification_id");
  const token = request.nextUrl.searchParams.get("token");
  const destination = new URL(
    `/verify/${encodeURIComponent(sessionId)}`,
    portalOrigin,
  );

  if (token) destination.hash = new URLSearchParams({ token }).toString();
  if (verificationId) {
    const fragment = new URLSearchParams(destination.hash.replace(/^#/, ""));
    fragment.set("verification_id", verificationId);
    destination.hash = fragment.toString();
  }

  return NextResponse.redirect(destination);
}
