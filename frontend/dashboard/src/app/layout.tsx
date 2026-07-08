import type { Metadata } from "next";
import "./globals.css";
import { DashboardShell } from "@/components/layout/dashboard-shell";

export const metadata: Metadata = {
  title: "IdentityCore Dashboard",
  description: "IdentityCore organization workspace dashboard.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-100 focus:rounded-xl focus:bg-blue-600 focus:px-4 focus:py-2 focus:text-sm focus:font-medium focus:text-white"
        >
          Skip to content
        </a>

        <DashboardShell>{children}</DashboardShell>
      </body>
    </html>
  );
}
