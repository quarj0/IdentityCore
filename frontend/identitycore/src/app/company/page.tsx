import Link from "next/link";
import { ArrowRight, Globe2, Landmark, Shield, Workflow } from "lucide-react";
import {
  Badge,
  Button,
} from "@identitycore/ui";
import { MarketingCTA } from "@/components/marketing/cta-section";
import { FeatureCard } from "@/components/marketing/feature-card";
import { MarketingFooter } from "@/components/marketing/marketing-footer";
import { MarketingHeader } from "@/components/marketing/marketing-header";
import { Section } from "@/components/marketing/section";
import { SectionHeader } from "@/components/marketing/section-header";

const values = [
  {
    title: "Infrastructure over features",
    description:
      "IdentityCore is designed as a foundation organizations can build on, not a closed verification tool.",
    icon: Workflow,
  },
  {
    title: "Privacy by design",
    description:
      "Identity systems should collect only what is needed, protect it carefully, and make usage transparent.",
    icon: Shield,
  },
  {
    title: "Government-ready thinking",
    description:
      "The platform is built with data sovereignty, dedicated deployments, and national identity systems in mind.",
    icon: Landmark,
  },
  {
    title: "Africa first, global later",
    description:
      "IdentityCore begins with African realities while remaining extensible for other regions and markets.",
    icon: Globe2,
  },
];

export default function CompanyPage() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <MarketingHeader activePath="/company" />

      <main id="main-content">
        <section className="relative overflow-hidden">
          <div className="absolute inset-x-0 top-0 -z-10 h-[560px] bg-[radial-gradient(circle_at_top_left,rgba(37,99,235,0.16),transparent_34%),linear-gradient(180deg,#ffffff_0%,#f8fafc_100%)]" />

          <div className="mx-auto max-w-7xl px-6 py-24 lg:py-32">
            <Badge variant="secondary" className="rounded-full px-3 py-1">
              Company
            </Badge>

            <h1 className="mt-6 max-w-5xl text-5xl font-semibold tracking-tight sm:text-6xl lg:text-7xl lg:leading-[0.98]">
              Building the infrastructure for digital trust.
            </h1>

            <p className="mt-7 max-w-2xl text-lg leading-8 text-muted-foreground">
              IdentityCore exists to help governments, enterprises, and digital
              platforms build trusted identity systems with control, privacy,
              provider flexibility, and secure deployment options.
            </p>

            <div className="mt-10 flex flex-wrap gap-3">
              <Button asChild size="lg" className="rounded-xl">
                <Link href="/platform">
                  Explore platform
                  <ArrowRight className="h-4 w-4" />
                </Link>
              </Button>
            </div>
          </div>
        </section>

        <Section>
          <div className="grid gap-12 lg:grid-cols-[0.85fr_1.15fr] lg:items-start">
            <SectionHeader
              eyebrow="Mission"
              title="Give organizations the identity layer they can control."
              description="IdentityCore starts with verification, but the long-term vision is broader: workflows, credentials, access, risk, provider orchestration, and trust services across Africa and beyond."
            />

            <div className="grid gap-6 sm:grid-cols-2">
              {values.map((value) => (
                <FeatureCard key={value.title} {...value} />
              ))}
            </div>
          </div>
        </Section>

        <section className="bg-slate-950 py-24 text-white">
          <div className="mx-auto max-w-7xl px-6">
            <p className="text-sm font-medium text-blue-300">Positioning</p>
            <h2 className="mt-3 max-w-4xl text-3xl font-semibold tracking-tight sm:text-4xl">
              We are not building another closed KYC vendor.
            </h2>
            <p className="mt-5 max-w-3xl text-lg leading-8 text-slate-300">
              IdentityCore is built to become an infrastructure layer. Customers
              should be able to use IdentityCore services, bring their own
              providers, connect government systems, and decide how their
              identity data is stored, processed, and governed.
            </p>
          </div>
        </section>

        <MarketingCTA
          title="Build on identity infrastructure designed for control."
          description="Start with verification workflows today and grow into broader digital trust services over time."
          secondaryHref="/how-it-works"
          secondaryLabel="See how it works"
        />
      </main>

      <MarketingFooter />
    </div>
  );
}
