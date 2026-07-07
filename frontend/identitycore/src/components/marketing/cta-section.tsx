import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { Button } from "@identitycore/ui";

interface MarketingCTAProps {
  title?: string;
  description?: string;
  secondaryHref?: string;
  secondaryLabel?: string;
}

export function MarketingCTA({
  title = "Build your identity platform without starting from zero.",
  description = "Use IdentityCore as the infrastructure layer for workflows, providers, policies, APIs, and trust services.",
  secondaryHref = "/platform",
  secondaryLabel = "Explore platform",
}: MarketingCTAProps) {
  return (
    <section className="py-24">
      <div className="mx-auto max-w-4xl px-6 text-center">
        <h2 className="text-4xl font-semibold tracking-tight sm:text-5xl">
          {title}
        </h2>

        <p className="mx-auto mt-5 max-w-2xl text-lg leading-8 text-muted-foreground">
          {description}
        </p>

        <div className="mt-10 flex justify-center gap-3">
          <Button asChild size="lg" className="rounded-xl">
            <Link href="/register">
              Create workspace
              <ArrowRight className="h-4 w-4" />
            </Link>
          </Button>

          <Button asChild variant="outline" size="lg" className="rounded-xl">
            <Link href={secondaryHref}>{secondaryLabel}</Link>
          </Button>
        </div>
      </div>
    </section>
  );
}
