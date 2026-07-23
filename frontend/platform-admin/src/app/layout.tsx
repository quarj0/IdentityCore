import type { Metadata } from "next";
import type { ReactNode } from "react";
import { PlatformAdminShell } from "@/components/layout/platform-admin-shell";
import "@/app/globals.css";

export const metadata: Metadata = {
  title: "Platform Admin | IdentityCore",
  description: "Internal platform administration console for IdentityCore.",
};

type RootLayoutProps = {
  children: ReactNode;
};

export default function RootLayout({ children }: RootLayoutProps) {
  return (
    <html lang="en" data-scroll-behavior="smooth">
      <body suppressHydrationWarning>
        <PlatformAdminShell>{children}</PlatformAdminShell>
      </body>
    </html>
  );
}
