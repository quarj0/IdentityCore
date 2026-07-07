import React from "react";
import Link from "next/link";
import { ArrowRight, Shield, Zap, Lock, Fingerprint, Code, Server, Check } from "lucide-react";
import { Button, Card, CardContent, CardDescription, CardHeader, CardTitle } from "@identitycore/ui";

export default function LandingPage() {
  return (
    <div className="flex flex-col min-h-screen">
      {/* Navigation */}
      <header className="px-6 lg:px-8 h-16 flex items-center border-b border-border bg-background/80 backdrop-blur-md sticky top-0 z-50">
        <div className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-primary text-primary-foreground">
            <Fingerprint className="h-4.5 w-4.5" />
          </div>
          <span className="font-semibold text-base tracking-tight">IdentityCore</span>
        </div>
        <nav className="ml-auto flex gap-4 sm:gap-6 items-center">
          <Link className="text-sm font-medium hover:underline underline-offset-4 text-muted-foreground hover:text-foreground transition-colors" href="/pricing">
            Pricing
          </Link>
          <Link className="text-sm font-medium hover:underline underline-offset-4 text-muted-foreground hover:text-foreground transition-colors" href="/security">
            Security
          </Link>
          <Link className="text-sm font-medium hover:underline underline-offset-4 text-muted-foreground hover:text-foreground transition-colors" href="/company">
            Company
          </Link>
          <Separator />
          <a href="http://localhost:3000" className="text-sm font-medium hover:underline underline-offset-4 text-muted-foreground hover:text-foreground transition-colors">
            Sign In
          </a>
          <Button asChild size="sm">
            <a href="http://localhost:3000">Get Started</a>
          </Button>
        </nav>
      </header>

      {/* Hero Section */}
      <section className="py-20 lg:py-32 px-6 lg:px-8 bg-slate-50 dark:bg-slate-950 flex flex-col items-center text-center">
        <div className="max-w-3xl space-y-6">
          <Badge variant="secondary" className="px-3 py-1 text-xs gap-1.5">
            <Sparkles className="h-3.5 w-3.5 text-primary" />
            Identity Verification for Developers
          </Badge>
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight text-foreground leading-[1.1]">
            Build secure verification into your product in minutes
          </h1>
          <p className="text-base sm:text-lg text-muted-foreground max-w-2xl mx-auto leading-relaxed">
            Enterprise-grade identity verification infrastructure. OCR document processing, real-time face matching, and liveness detection. Developer-first API integration.
          </p>
          <div className="flex flex-wrap items-center justify-center gap-3 pt-4">
            <Button size="lg" className="gap-2" asChild>
              <a href="http://localhost:3000">
                Start verifying now
                <ArrowRight className="h-4 w-4" />
              </a>
            </Button>
            <Button size="lg" variant="outline" className="gap-2" asChild>
              <a href="http://localhost:3003">
                <Code className="h-4 w-4" />
                Read API docs
              </a>
            </Button>
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section className="py-20 px-6 lg:px-8 max-w-7xl mx-auto w-full">
        <div className="text-center max-w-2xl mx-auto mb-16 space-y-3">
          <h2 className="text-2xl sm:text-3xl font-bold tracking-tight">Everything you need to verify users securely</h2>
          <p className="text-sm sm:text-base text-muted-foreground">
            A comprehensive suite of identity tools designed to eliminate fraud and streamline compliance.
          </p>
        </div>

        <div className="grid gap-6 md:grid-cols-3">
          <Card className="bg-transparent border-slate-200/80">
            <CardHeader>
              <div className="h-10 w-10 rounded-lg bg-primary/5 flex items-center justify-center mb-3">
                <Shield className="h-5 w-5 text-primary" />
              </div>
              <CardTitle className="text-base font-semibold">Smart Document OCR</CardTitle>
              <CardDescription className="text-xs">
                Extract details from passports, driver's licenses, and identity cards globally with precision models.
              </CardDescription>
            </CardHeader>
          </Card>

          <Card className="bg-transparent border-slate-200/80">
            <CardHeader>
              <div className="h-10 w-10 rounded-lg bg-primary/5 flex items-center justify-center mb-3">
                <Zap className="h-5 w-5 text-primary" />
              </div>
              <CardTitle className="text-base font-semibold">Real-Time Liveness Check</CardTitle>
              <CardDescription className="text-xs">
                Verify presence instantly using lightweight biometric models directly in the user's browser.
              </CardDescription>
            </CardHeader>
          </Card>

          <Card className="bg-transparent border-slate-200/80">
            <CardHeader>
              <div className="h-10 w-10 rounded-lg bg-primary/5 flex items-center justify-center mb-3">
                <Code className="h-5 w-5 text-primary" />
              </div>
              <CardTitle className="text-base font-semibold">Flexible Policy Builder</CardTitle>
              <CardDescription className="text-xs">
                Create customized rules and flows that fit your unique geographic and regulatory demands without writing code.
              </CardDescription>
            </CardHeader>
          </Card>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border py-8 px-6 lg:px-8 text-center text-xs text-muted-foreground mt-auto">
        <p>© 2026 IdentityCore, Inc. All rights reserved.</p>
      </footer>
    </div>
  );
}

import { Badge } from "@identitycore/ui";
import { Separator } from "@identitycore/ui";
import { Sparkles } from "lucide-react";
