import {
  Building2,
  MessageSquare,
  ShieldCheck,
} from "lucide-react";
import { Badge } from "@identitycore/ui";
import { ContactForm } from "@/components/contact/contact-form";
import { MarketingHeader } from "@/components/marketing/marketing-header";
import { MarketingFooter } from "@/components/marketing/marketing-footer";

export default function ContactPage() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <MarketingHeader activePath="/contact" />

      <main id="main-content">
        <section className="relative overflow-hidden">
          <div className="absolute inset-x-0 top-0 -z-10 h-[640px] bg-[radial-gradient(circle_at_top_left,rgba(37,99,235,0.16),transparent_34%),linear-gradient(180deg,#ffffff_0%,#f8fafc_100%)]" />

          <div className="mx-auto grid max-w-7xl gap-16 px-6 py-24 lg:grid-cols-[0.9fr_1.1fr] lg:items-start lg:py-32">
            <div>
              <Badge variant="secondary" className="rounded-full px-3 py-1">
                Contact
              </Badge>

              <h1 className="mt-6 max-w-5xl text-5xl font-semibold tracking-tight sm:text-6xl lg:text-7xl lg:leading-[0.98]">
                Talk to us about identity infrastructure.
              </h1>

              <p className="mt-7 max-w-2xl text-lg leading-8 text-muted-foreground">
                Whether you are exploring hosted workflows, provider
                orchestration, enterprise governance, or future dedicated
                deployment options, we can help you plan the right path.
              </p>

              <div className="mt-10 grid gap-4">
                {[
                  [
                    "Sales and partnerships",
                    "Discuss pricing, use cases, and pilots.",
                    Building2,
                  ],
                  [
                    "Security and compliance",
                    "Ask about privacy, governance, and deployment controls.",
                    ShieldCheck,
                  ],
                  [
                    "Technical questions",
                    "Understand APIs, workflows, providers, and integration paths.",
                    MessageSquare,
                  ],
                ].map(([title, description, Icon]) => {
                  const LucideIcon = Icon as typeof Building2;

                  return (
                    <div
                      key={title as string}
                      className="flex gap-3 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm"
                    >
                      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-blue-50 text-blue-700">
                        <LucideIcon className="h-5 w-5" />
                      </div>
                      <div>
                        <p className="text-sm font-semibold">
                          {title as string}
                        </p>
                        <p className="mt-1 text-sm leading-6 text-muted-foreground">
                          {description as string}
                        </p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            <ContactForm />
          </div>
        </section>
      </main>

      <MarketingFooter />
    </div>
  );
}
