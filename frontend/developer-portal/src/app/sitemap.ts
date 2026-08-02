import type { MetadataRoute } from "next";

const staticRoutes = [
  "/",
  "/quickstart",
  "/authentication",
  "/api-reference",
  "/openapi",
  "/webhooks",
  "/webhooks/signatures",
  "/sandbox",
  "/examples",
  "/changelog",
  "/errors",
  "/sdk",
  "/cli",
];

export default function sitemap(): MetadataRoute.Sitemap {
  const baseUrl =
    process.env.NEXT_PUBLIC_DEVELOPER_PORTAL_URL ??
    "https://docs.identitycore.com";

  return staticRoutes.map((route) => ({
    url: `${baseUrl.replace(/\/$/, "")}${route}`,
    changeFrequency: route === "/changelog" ? "weekly" : "monthly",
    priority: route === "/" ? 1 : 0.7,
  }));
}
