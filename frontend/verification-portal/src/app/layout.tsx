import type { Metadata } from "next";
import { headers } from "next/headers";
import { ThemeProvider } from "@identitycore/ui";
import { direction, resolveLocale } from "@/lib/i18n";
import { PortalLocaleProvider, PortalSkipLink } from "@/lib/portal-locale";
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
        <ThemeProvider
          defaultTheme="light"
          storageKey="identitycore-verify-theme"
        >
          <PortalLocaleProvider locale={locale}>
            <PortalSkipLink />
            {children}
          </PortalLocaleProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
