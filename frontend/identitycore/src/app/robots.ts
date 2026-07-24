import type { MetadataRoute } from "next";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: "*",
      allow: "/",
      disallow: ["/onboarding/", "/verification", "/verify-email", "/login", "/register", "/reset-password", "/forgot-password", "/change-password"],
    },
  };
}
