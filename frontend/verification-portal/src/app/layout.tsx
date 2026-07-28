import type { Metadata } from "next";
import { headers } from "next/headers";
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
    <html lang={locale} dir={direction(locale)}>
      <body>
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-100 focus:rounded-xl focus:bg-blue-600 focus:px-4 focus:py-2 focus:text-sm focus:font-medium focus:text-white"
        >
          {translate(locale, "skip")}
        </a>
        {children}
      </body>
    </html>
  );
}
