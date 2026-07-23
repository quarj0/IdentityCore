import type { Metadata } from "next";
import "./globals.css";
import { DashboardFrame } from "@/components/layout/dashboard-frame";
import { DashboardSession } from "@/components/auth/dashboard-session";
import { Toaster } from "@identitycore/ui";

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
    <html lang="en" data-scroll-behavior="smooth">
      <body>
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-100 focus:rounded-xl focus:bg-blue-600 focus:px-4 focus:py-2 focus:text-sm focus:font-medium focus:text-white"
        >
          Skip to content
        </a>

        <DashboardSession><DashboardFrame>{children}</DashboardFrame></DashboardSession>
        <Toaster />
      </body>
    </html>
  );
}
