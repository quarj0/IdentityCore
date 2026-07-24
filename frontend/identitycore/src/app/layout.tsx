import type { Metadata } from "next";
import { ThemeProvider, Toaster } from "@identitycore/ui";
import "./globals.css";

export const metadata: Metadata = {
  applicationName: "IdentityCore",
  title: {
    default: "IdentityCore | Modern Identity Verification Infrastructure",
    template: "%s | IdentityCore",
  },
  description:
    "Enterprise-grade identity verification, OCR, face matching, and liveness check APIs built for modern developer-first organizations.",
  keywords: [
    "identity verification",
    "KYC",
    "compliance",
    "biometrics",
    "liveness check",
    "OCR API",
  ],
  robots: {
    index: true,
    follow: true,
  },
  openGraph: {
    type: "website",
    siteName: "IdentityCore",
    title: "IdentityCore | Modern Identity Verification Infrastructure",
    description:
      "Enterprise-grade identity verification infrastructure for modern organizations.",
  },
  twitter: {
    card: "summary",
    title: "IdentityCore | Modern Identity Verification Infrastructure",
    description:
      "Enterprise-grade identity verification infrastructure for modern organizations.",
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
          {children}
          <Toaster />
        </ThemeProvider>
      </body>
    </html>
  );
}
