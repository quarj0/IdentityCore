import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { Geist_Mono } from "next/font/google";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  display: "swap",
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: "IdentityCore | Modern Identity Verification Infrastructure",
    template: "%s | IdentityCore",
  },
  description:
    "Enterprise-grade identity verification, OCR, face matching, and liveness check APIs built for modern developer-first organizations.",
  keywords: ["identity verification", "KYC", "compliance", "biometrics", "liveness check", "OCR API"],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${inter.variable} ${geistMono.variable} h-full`}
      suppressHydrationWarning
    >
      <body className="min-h-full bg-background text-foreground antialiased flex flex-col justify-between">
        {children}
      </body>
    </html>
  );
}
