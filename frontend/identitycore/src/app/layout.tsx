import type { Metadata } from "next";
import { Suspense } from "react";
import { ThemeProvider, Toaster } from "@identitycore/ui";
import { SessionExpiryBoundary } from "@/components/auth/session-expiry-boundary";
import "./globals.css";

const siteUrl = process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3001";
const allowIndexing = process.env.NEXT_PUBLIC_ALLOW_INDEXING === "true";

export const metadata: Metadata = {
  applicationName: "IdentityCore",
  metadataBase: new URL(siteUrl),
  title: {
    default: "IdentityCore | Identity Infrastructure and Orchestration",
    template: "%s | IdentityCore",
  },
  description:
    "Build identity services with one control plane for workflows, policies, evidence, and managed or bring-your-own providers.",
  keywords: [
    "identity infrastructure",
    "identity orchestration",
    "bring your own identity provider",
    "identity verification",
    "KYC",
    "compliance",
    "biometrics",
    "liveness check",
    "OCR API",
  ],
  robots: {
    index: allowIndexing,
    follow: allowIndexing,
  },
  openGraph: {
    type: "website",
    siteName: "IdentityCore",
    title: "IdentityCore | Identity Infrastructure and Orchestration",
    description:
      "Compose identity workflows, policies, evidence, and providers behind one stable platform contract.",
    url: "/",
    images: [{ url: "/opengraph-image", width: 1200, height: 630 }],
  },
  twitter: {
    card: "summary_large_image",
    title: "IdentityCore | Identity Infrastructure and Orchestration",
    description:
      "Compose identity workflows, policies, evidence, and providers behind one stable platform contract.",
    images: ["/opengraph-image"],
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      data-scroll-behavior="smooth"
      className="h-full"
      suppressHydrationWarning
    >
      <body
        className="min-h-full bg-background text-foreground antialiased"
        suppressHydrationWarning
      >
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-100 focus:rounded-xl focus:bg-blue-600 focus:px-4 focus:py-2 focus:text-sm focus:font-medium focus:text-white"
        >
          Skip to content
        </a>
        <ThemeProvider defaultTheme="light" storageKey="identitycore-web-theme">
          <Suspense fallback={null}>
            <SessionExpiryBoundary />
          </Suspense>
          {children}
          <Toaster />
        </ThemeProvider>
      </body>
    </html>
  );
}
