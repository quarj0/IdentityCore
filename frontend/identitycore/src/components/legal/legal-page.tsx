import { Badge, Card, CardContent } from "@identitycore/ui";
import { MarketingFooter } from "@/components/marketing/marketing-footer";
import { MarketingHeader } from "@/components/marketing/marketing-header";

interface LegalSection {
  title: string;
  body: string[];
}

interface LegalPageProps {
  title: string;
  description: string;
  updatedAt: string;
  sections: LegalSection[];
}

export function LegalPage({
  title,
  description,
  updatedAt,
  sections,
}: LegalPageProps) {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <MarketingHeader />

      <main id="main-content">
        <section className="relative overflow-hidden">
          <div className="absolute inset-x-0 top-0 -z-10 h-[420px] bg-[radial-gradient(circle_at_top_left,rgba(37,99,235,0.14),transparent_34%),linear-gradient(180deg,#ffffff_0%,#f8fafc_100%)]" />

          <div className="mx-auto max-w-4xl px-4 py-20 sm:px-6 lg:py-28">
            <Badge variant="secondary" className="rounded-full px-3 py-1">
              Legal
            </Badge>

            <h1 className="mt-6 text-4xl font-semibold tracking-tight sm:text-5xl lg:text-6xl">
              {title}
            </h1>

            <p className="mt-6 text-lg leading-8 text-muted-foreground">
              {description}
            </p>

            <p className="mt-4 text-sm text-muted-foreground">
              Last updated: {updatedAt}
            </p>
          </div>
        </section>

        <section className="pb-24">
          <div className="mx-auto max-w-4xl px-4 sm:px-6">
            <Card className="rounded-3xl border-slate-200 bg-white shadow-sm">
              <CardContent className="space-y-10 p-6 sm:p-10">
                {sections.map((section) => (
                  <section key={section.title}>
                    <h2 className="text-xl font-semibold tracking-tight">
                      {section.title}
                    </h2>

                    <div className="mt-4 space-y-4">
                      {section.body.map((paragraph) => (
                        <p
                          key={paragraph}
                          className="text-sm leading-7 text-muted-foreground sm:text-base"
                        >
                          {paragraph}
                        </p>
                      ))}
                    </div>
                  </section>
                ))}
              </CardContent>
            </Card>
          </div>
        </section>
      </main>

      <MarketingFooter />
    </div>
  );
}
