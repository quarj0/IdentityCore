import type { NextConfig } from "next";
import path from "path";
import { verificationApiSecurityHeaders } from "./src/security-headers";

const nextConfig: NextConfig = {
  output: "standalone",
  poweredByHeader: false,
  async headers() {
    const values = verificationApiSecurityHeaders();
    if (process.env.NODE_ENV === "production")
      values["Strict-Transport-Security"] = "max-age=31536000";
    return [
      {
        source: "/api/verification/:path*",
        headers: Object.entries(values).map(([key, value]) => ({ key, value })),
      },
    ];
  },
  turbopack: {
    root: path.join(__dirname, ".."),
  },
  transpilePackages: ["@identitycore/ui"],
};

export default nextConfig;
