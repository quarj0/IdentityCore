import type { NextConfig } from "next";
import { PHASE_DEVELOPMENT_SERVER } from "next/constants";
import path from "path";

const nextConfig = (phase: string): NextConfig => {
  const isDevelopment = phase === PHASE_DEVELOPMENT_SERVER;
  const securityHeaders = [
    { key: "X-Content-Type-Options", value: "nosniff" },
    { key: "X-Frame-Options", value: "DENY" },
    { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
    {
      key: "Permissions-Policy",
      value: "camera=(), microphone=(), geolocation=(), payment=()",
    },
    { key: "Cross-Origin-Opener-Policy", value: "same-origin" },
    { key: "X-DNS-Prefetch-Control", value: "off" },
    {
      key: "Content-Security-Policy",
      value: [
        "default-src 'self'",
        "base-uri 'self'",
        "frame-ancestors 'none'",
        "form-action 'self'",
        "object-src 'none'",
        `script-src 'self' 'unsafe-inline'${isDevelopment ? " 'unsafe-eval'" : ""}`,
        "style-src 'self' 'unsafe-inline'",
        "img-src 'self' data: blob: https:",
        "font-src 'self' data:",
        `connect-src 'self' ${process.env.NEXT_PUBLIC_API_ORIGIN ?? "http://localhost:8000"} ${isDevelopment ? "ws: wss:" : ""}`,
        ...(process.env.NEXT_PUBLIC_SITE_URL?.startsWith("https://")
          ? ["upgrade-insecure-requests"]
          : []),
      ].join("; "),
    },
    ...(!isDevelopment
      ? [
          {
            key: "Strict-Transport-Security",
            value: "max-age=63072000; includeSubDomains; preload",
          },
        ]
      : []),
  ];

  return {
    poweredByHeader: false,
    experimental: {
      useTypeScriptCli: true,
    },
    async headers() {
      return [{ source: "/(.*)", headers: securityHeaders }];
    },
    async redirects() {
      const dashboard = (
        process.env.NEXT_PUBLIC_DASHBOARD_URL ?? "http://localhost:3000"
      ).replace(/\/$/, "");
      return [
        "/login",
        "/register",
        "/forgot-password",
        "/reset-password",
        "/change-password",
        "/verify-email",
      ].map((source) => ({
        source,
        destination: `${dashboard}${source}`,
        permanent: false,
      })).concat([
        {
          source: "/onboarding/:path*",
          destination: `${dashboard}/onboarding/:path*`,
          permanent: false,
        },
      ]);
    },
    turbopack: {
      root: path.join(__dirname, ".."),
    },
    transpilePackages: ["@identitycore/ui"],
  };
};

export default nextConfig;
