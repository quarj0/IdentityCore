import type { MetadataRoute } from "next";

export default function robots(): MetadataRoute.Robots {
  const allowIndexing = process.env.NEXT_PUBLIC_ALLOW_INDEXING === "true";
  const siteUrl = process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3001";
  return {
    rules: allowIndexing
      ? {
          userAgent: "*",
          allow: "/",
          disallow: [
            "/onboarding/",
            "/verification",
            "/verify-email",
            "/login",
            "/register",
            "/reset-password",
            "/forgot-password",
            "/change-password",
          ],
        }
      : { userAgent: "*", disallow: "/" },
    sitemap: `${siteUrl.replace(/\/$/, "")}/sitemap.xml`,
  };
}
