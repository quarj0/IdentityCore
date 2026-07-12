import { DocsCard } from "@/components/docs/docs-card";
import { DocsCTA } from "@/components/docs/docs-cta";
import { DocsLayout } from "@/components/docs/docs-layout";
import { docsNav } from "@/data/docs-nav";

export default function DeveloperPortalHome() {
  const cards = docsNav.flatMap((group) => group.items).slice(1);

  return (
    <DocsLayout
      title="Build with IdentityCore"
      description="Use IdentityCore APIs, webhooks, sandbox tools, and verifications to integrate digital identity infrastructure into your product."
    >
      <div className="grid gap-6 md:grid-cols-2">
        {cards.map((item) => (
          <DocsCard key={item.href} {...item} />
        ))}
      </div>

      <DocsCTA />
    </DocsLayout>
  );
}
