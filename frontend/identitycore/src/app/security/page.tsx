import React from "react";
import Link from "next/link";
import { Shield, ShieldAlert, Key, Lock, Fingerprint, Award, CheckCircle } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@identitycore/ui";

export default function SecurityPage() {
  return (
    <div className="flex flex-col min-h-screen">
      <header className="px-6 lg:px-8 h-16 flex items-center border-b border-border bg-background/80 backdrop-blur-md">
        <Link href="/" className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-primary text-primary-foreground">
            <Fingerprint className="h-4.5 w-4.5" />
          </div>
          <span className="font-semibold text-base tracking-tight">IdentityCore</span>
        </Link>
      </header>

      <main className="flex-1 max-w-4xl mx-auto w-full px-6 py-12 lg:py-20 space-y-12">
        <div className="space-y-4">
          <h1 className="text-3xl sm:text-4xl font-bold tracking-tight">Security & Compliance</h1>
          <p className="text-base text-muted-foreground leading-relaxed">
            Security isn't a feature; it's our core foundation. We process and store sensitive identity documentation under the highest regulatory and cryptographic standards.
          </p>
        </div>

        <div className="grid gap-6 md:grid-cols-2 pt-6">
          <Card className="border-slate-200/80">
            <CardHeader>
              <div className="h-10 w-10 rounded-lg bg-primary/5 flex items-center justify-center mb-3">
                <Lock className="h-5 w-5 text-primary" />
              </div>
              <CardTitle className="text-base font-semibold">End-to-End Encryption</CardTitle>
              <CardDescription className="text-xs">
                All data, from uploaded documents to biometric frames, is encrypted in transit using TLS 1.3 and at rest with AES-256.
              </CardDescription>
            </CardHeader>
          </Card>

          <Card className="border-slate-200/80">
            <CardHeader>
              <div className="h-10 w-10 rounded-lg bg-primary/5 flex items-center justify-center mb-3">
                <Award className="h-5 w-5 text-primary" />
              </div>
              <CardTitle className="text-base font-semibold">Compliance Ready</CardTitle>
              <CardDescription className="text-xs">
                IdentityCore is designed to align with SOC2 Type II, GDPR, CCPA, and standard KYC/AML regulatory standards.
              </CardDescription>
            </CardHeader>
          </Card>
        </div>
      </main>
    </div>
  );
}
