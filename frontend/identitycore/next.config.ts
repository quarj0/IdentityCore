import type { NextConfig } from "next";
import path from "path";

const nextConfig = (): NextConfig => {
  return {
    poweredByHeader: false,
    experimental: {
      useTypeScriptCli: true,
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
      ]
        .map((source) => ({
          source,
          destination: `${dashboard}${source}`,
          permanent: false,
        }))
        .concat([
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
