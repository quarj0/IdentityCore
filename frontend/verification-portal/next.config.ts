import type { NextConfig } from "next";
import path from "path";

const nextConfig: NextConfig = {
  output: "standalone",
  poweredByHeader: false,
  turbopack: {
    root: path.join(__dirname, ".."),
  },
  transpilePackages: ["@identitycore/ui"],
};

export default nextConfig;
