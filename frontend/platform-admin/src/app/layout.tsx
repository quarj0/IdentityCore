import type { Metadata } from "next";
import type { ReactNode } from "react";
import { PlatformAdminShell } from "@/components/layout/platform-admin-shell";
import { PlatformAdminAuthGate } from "@/components/auth/platform-admin-auth-gate";
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
        <PlatformAdminAuthGate>
          <PlatformAdminShell>{children}</PlatformAdminShell>
        </PlatformAdminAuthGate>
      </body>
    </html>
  );
}
