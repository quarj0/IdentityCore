import type { Metadata } from "next";
import { headers } from "next/headers";
import { ThemeProvider } from "@identitycore/ui";
import { direction, resolveLocale, translate } from "@/lib/i18n";
import "./globals.css";

export const metadata: Metadata = {
  title: "IdentityCore Verify",
  description: "Secure verification portal powered by IdentityCore.",
};

export default async function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  const locale = resolveLocale((await headers()).get("accept-language"));
  return (
    <html lang={locale} dir={direction(locale)} suppressHydrationWarning>
      <body className="bg-background text-foreground" suppressHydrationWarning>
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-100 focus:rounded-xl focus:bg-primary focus:px-4 focus:py-2 focus:text-sm focus:font-medium focus:text-primary-foreground"
        >
          {translate(locale, "skip")}
        </a>
        <ThemeProvider
          defaultTheme="light"
          storageKey="identitycore-verify-theme"
        >
          {children}
        </ThemeProvider>
      </body>
    </html>
  );
}
