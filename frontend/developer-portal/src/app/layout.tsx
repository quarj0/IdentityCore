import type { Metadata } from "next";
import { IBM_Plex_Mono, Manrope } from "next/font/google";
import { ThemeProvider, Toaster } from "@identitycore/ui";
import "./globals.css";

const manrope = Manrope({
  variable: "--font-brand-sans",
  subsets: ["latin"],
  display: "swap",
});

const plexMono = IBM_Plex_Mono({
  variable: "--font-brand-mono",
  weight: ["400", "500"],
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: "IdentityCore Developers",
    template: "%s | IdentityCore Docs",
  },
  description: "API reference, SDK guides, and quickstart documentation for integrating IdentityCore.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${manrope.variable} ${plexMono.variable} h-full`}
      suppressHydrationWarning
    >
      <body className="min-h-full bg-background text-foreground antialiased">
        <ThemeProvider defaultTheme="light" storageKey="identitycore-docs-theme">
          {children}
          <Toaster />
        </ThemeProvider>
      </body>
    </html>
  );
}
