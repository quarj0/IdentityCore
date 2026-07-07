import React from "react";
import Link from "next/link";
import { Fingerprint, Building, Users, Calendar } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@identitycore/ui";

export default function CompanyPage() {
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
          <h1 className="text-3xl sm:text-4xl font-bold tracking-tight">About IdentityCore</h1>
          <p className="text-base text-muted-foreground leading-relaxed">
            Our mission is to make identity infrastructure simple, safe, and trustworthy. We build developer-first APIs and portals that enable organizations to verify users reliably and keep fraud out.
          </p>
        </div>

        <div className="grid gap-6 md:grid-cols-3 pt-6">
          <Card className="border-slate-200/80">
            <CardHeader>
              <div className="h-8 w-8 rounded-lg bg-primary/5 flex items-center justify-center mb-2">
                <Building className="h-4 w-4 text-primary" />
              </div>
              <CardTitle className="text-sm font-semibold">Headquarters</CardTitle>
              <CardDescription className="text-xs">San Francisco, California</CardDescription>
            </CardHeader>
          </Card>

          <Card className="border-slate-200/80">
            <CardHeader>
              <div className="h-8 w-8 rounded-lg bg-primary/5 flex items-center justify-center mb-2">
                <Users className="h-4 w-4 text-primary" />
              </div>
              <CardTitle className="text-sm font-semibold">Team Size</CardTitle>
              <CardDescription className="text-xs">45 global team members</CardDescription>
            </CardHeader>
          </Card>

          <Card className="border-slate-200/80">
            <CardHeader>
              <div className="h-8 w-8 rounded-lg bg-primary/5 flex items-center justify-center mb-2">
                <Calendar className="h-4 w-4 text-primary" />
              </div>
              <CardTitle className="text-sm font-semibold">Founded</CardTitle>
              <CardDescription className="text-xs">Established in 2024</CardDescription>
            </CardHeader>
          </Card>
        </div>
      </main>
    </div>
  );
}
