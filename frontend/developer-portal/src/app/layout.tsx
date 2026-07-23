import type { Metadata } from "next";
import "./globals.css";
import { DocsHeader } from "@/components/navigation/docs-header";

export const metadata: Metadata = {
  title: "IdentityCore Developer Portal",
  description: "Developer documentation for IdentityCore APIs and workflows.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" data-scroll-behavior="smooth">
      <body>
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-100 focus:rounded-xl focus:bg-blue-600 focus:px-4 focus:py-2 focus:text-sm focus:font-medium focus:text-white"
        >
          Skip to content
        </a>

        <DocsHeader />
        {children}
      </body>
    </html>
  );
}
