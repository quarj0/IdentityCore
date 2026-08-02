import { type NextRequest, NextResponse } from "next/server";

import { securityHeaders } from "../../security-headers";

export function proxy(request: NextRequest) {
  if (process.env.NODE_ENV === "production") {
    const configuredApiUrl =
      process.env.NEXT_PUBLIC_API_ORIGIN ?? process.env.NEXT_PUBLIC_API_URL;
    if (!configuredApiUrl) {
      throw new Error(
        "NEXT_PUBLIC_API_ORIGIN must be configured for the developer portal in production.",
      );
    }

    const parsedApiUrl = new URL(configuredApiUrl);
    if (parsedApiUrl.protocol !== "https:") {
      throw new Error(
        "The developer portal API URL must use HTTPS in production.",
      );
    }
  }

  const nonce = crypto.randomUUID().replaceAll("-", "");
  const headers = securityHeaders(nonce, {
    apiOrigin: process.env.NEXT_PUBLIC_API_ORIGIN,
    camera: false,
    development: process.env.NODE_ENV === "development",
  });
  const requestHeaders = new Headers(request.headers);

  requestHeaders.set("x-nonce", nonce);
  requestHeaders.set(
    "Content-Security-Policy",
    headers["Content-Security-Policy"],
  );

  const response = NextResponse.next({ request: { headers: requestHeaders } });
  for (const [name, value] of Object.entries(headers)) {
    response.headers.set(name, value);
  }
  if (process.env.NODE_ENV === "production") {
    response.headers.set(
      "Strict-Transport-Security",
      "max-age=63072000; includeSubDomains; preload",
    );
  }
  return response;
}

export const config = {
  matcher: [
    {
      source:
        "/((?!_next/static|_next/image|favicon.ico|sitemap.xml|robots.txt).*)",
      missing: [
        { type: "header", key: "next-router-prefetch" },
        { type: "header", key: "purpose", value: "prefetch" },
      ],
    },
  ],
};
