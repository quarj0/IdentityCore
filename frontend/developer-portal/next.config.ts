import type { NextConfig } from "next";
import path from "path";

const nextConfig: NextConfig = {
  poweredByHeader: false,
  experimental: {
    useTypeScriptCli: true,
  },
  turbopack: {
    root: path.join(__dirname, ".."),
  },
  transpilePackages: ["@identitycore/ui"],
};

export default nextConfig;
