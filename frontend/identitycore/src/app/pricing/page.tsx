import Link from "next/link";
import { Check } from "lucide-react";
import {
  Button,
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@identitycore/ui";
import { MarketingHeader } from "@/components/marketing/marketing-header";

const plans = [
  {
    name: "Developer",
    price: "$0",
    description: "For evaluation and low-volume testing.",
    features: [
      "100 verifications per month",
      "Hosted verification flow",
      "API and webhook access",
      "Community support",
    ],
    cta: "Get started",
  },
  {
    name: "Growth",
    price: "$149",
    description: "For teams running verification in production.",
    features: [
      "5,000 verifications included",
      "Biometric face match and liveness",
      "Review policies and queues",
      "Email support",
    ],
    cta: "Choose Growth",
    featured: true,
  },
  {
    name: "Enterprise",
    price: "Custom",
    description: "For high-volume and regulated deployments.",
    features: [
      "Volume-based pricing",
      "Dedicated compliance support",
      "Custom roles and audit exports",
      "Priority onboarding",
    ],
    cta: "Contact sales",
  },
];

export default function PricingPage() {
  return (
    <div className="min-h-screen bg-background">
      <MarketingHeader activePath="/pricing" />

      <div className="mx-auto max-w-6xl px-6 py-20">
        <div className="max-w-2xl">
          <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">
            Pricing
          </h1>
          <p className="mt-4 text-lg text-muted-foreground leading-7">
            Predictable pricing that scales with your verification volume. No
            hidden fees.
          </p>
        </div>

        <div className="mt-14 grid gap-6 lg:grid-cols-3">
          {plans.map((plan) => (
            <Card
              key={plan.name}
              className={
                plan.featured ? "border-foreground/20 shadow-sm" : "shadow-none"
              }
            >
              <CardHeader>
                <CardTitle className="text-lg">{plan.name}</CardTitle>
                <div className="flex items-baseline gap-1 pt-2">
                  <span className="text-3xl font-semibold tabular-nums tracking-tight">
                    {plan.price}
                  </span>
                  {plan.price !== "Custom" ? (
                    <span className="text-sm text-muted-foreground">
                      /month
                    </span>
                  ) : null}
                </div>
                <CardDescription className="pt-2 leading-6">
                  {plan.description}
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {plan.features.map((feature) => (
                  <div
                    key={feature}
                    className="flex gap-2.5 text-sm text-muted-foreground"
                  >
                    <Check
                      className="mt-0.5 h-4 w-4 shrink-0 text-foreground"
                      strokeWidth={2}
                    />
                    {feature}
                  </div>
                ))}
              </CardContent>
              <CardFooter>
                <Button
                  className="w-full"
                  variant={plan.featured ? "default" : "outline"}
                >
                  {plan.cta}
                </Button>
              </CardFooter>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}
