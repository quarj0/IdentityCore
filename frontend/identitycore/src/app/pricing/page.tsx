import React from "react";
import Link from "next/link";
import { Check, Fingerprint } from "lucide-react";
import { Button, Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle, Badge } from "@identitycore/ui";

const plans = [
  {
    name: "Developer",
    price: "$0",
    description: "Perfect for testing and small proof-of-concept projects.",
    features: [
      "100 free verifications / month",
      "Standard document OCR",
      "API & Webhook access",
      "Community support",
    ],
    cta: "Start Free",
    popular: false,
  },
  {
    name: "Growth",
    price: "$149",
    description: "Designed for scaling startups and growing businesses.",
    features: [
      "5,000 verifications included",
      "Biometric face matching",
      "Liveness detection models",
      "Custom verification policies",
      "Email support",
    ],
    cta: "Get Started",
    popular: true,
  },
  {
    name: "Enterprise",
    price: "Custom",
    description: "For platforms needing custom compliance & higher volume.",
    features: [
      "Unlimited verifications",
      "SLA-backed uptime guarantees",
      "Dedicated account manager",
      "Custom domain & white-labeling",
      "24/7 priority support",
    ],
    cta: "Contact Sales",
    popular: false,
  },
];

export default function PricingPage() {
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

      <main className="flex-1 max-w-7xl mx-auto w-full px-6 py-12 lg:py-20 space-y-12">
        <div className="text-center max-w-2xl mx-auto space-y-3">
          <h1 className="text-3xl sm:text-4xl font-bold tracking-tight">Simple, transparent pricing</h1>
          <p className="text-sm sm:text-base text-muted-foreground">
            Choose the plan that fits your integration needs. All plans include API sandbox access.
          </p>
        </div>

        <div className="grid gap-6 md:grid-cols-3 pt-6">
          {plans.map((plan) => (
            <Card key={plan.name} className={`flex flex-col relative ${plan.popular ? "border-primary shadow-md" : "border-slate-200/80"}`}>
              {plan.popular && (
                <Badge className="absolute -top-3 left-1/2 -translate-x-1/2" variant="default">
                  Most Popular
                </Badge>
              )}
              <CardHeader>
                <CardTitle className="text-lg">{plan.name}</CardTitle>
                <div className="mt-3 flex items-baseline gap-1">
                  <span className="text-3xl font-extrabold tracking-tight">{plan.price}</span>
                  {plan.price !== "Custom" && <span className="text-sm text-muted-foreground">/mo</span>}
                </div>
                <CardDescription className="mt-2 text-xs">{plan.description}</CardDescription>
              </CardHeader>
              <CardContent className="flex-1 space-y-4">
                <ul className="space-y-2.5 text-xs text-muted-foreground">
                  {plan.features.map((feat) => (
                    <li key={feat} className="flex items-center gap-2">
                      <Check className="h-4 w-4 text-emerald-600 dark:text-emerald-400 shrink-0" />
                      <span>{feat}</span>
                    </li>
                  ))}
                </ul>
              </CardContent>
              <CardFooter className="pt-4 border-t border-border mt-auto">
                <Button className="w-full" variant={plan.popular ? "default" : "outline"}>
                  {plan.cta}
                </Button>
              </CardFooter>
            </Card>
          ))}
        </div>
      </main>
    </div>
  );
}
