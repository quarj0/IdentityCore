import type { MetadataRoute } from "next";
import { solutions } from "@/data/solutions";
import { workflowTemplates } from "@/data/templates";

const publicRoutes = [
  "",
  "/company",
  "/contact",
  "/developers",
  "/how-it-works",
  "/legal/cookies",
  "/legal/privacy",
  "/legal/terms",
  "/platform",
  "/pricing",
  "/security",
  "/solutions",
  "/templates",
];

export default function sitemap(): MetadataRoute.Sitemap {
  const origin = (
    process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3001"
  ).replace(/\/$/, "");
  const routes = [
    ...publicRoutes,
    ...solutions.map((solution) => `/solutions/${solution.slug}`),
    ...workflowTemplates.map((template) => `/templates/${template.slug}`),
  ];

  return routes.map((route) => ({
    url: `${origin}${route}`,
    changeFrequency: route === "" ? "weekly" : "monthly",
    priority: route === "" ? 1 : 0.7,
  }));
}
