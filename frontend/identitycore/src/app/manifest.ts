import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "IdentityCore",
    short_name: "IdentityCore",
    description:
      "Identity infrastructure for workflows, policies, evidence, and provider orchestration.",
    start_url: "/",
    display: "standalone",
    background_color: "#ffffff",
    theme_color: "#0f172a",
    icons: [{ src: "/favicon.ico", sizes: "256x256", type: "image/x-icon" }],
  };
}
