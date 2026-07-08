import { DocsLayout } from "@/components/docs/docs-layout";
import { LanguageExamples } from "@/components/docs/language-examples";
import { examples } from "@/data/examples";

export default function ExamplesPage() {
  return (
    <DocsLayout
      title="Examples"
      description="Common API and webhook examples for integrating IdentityCore into your product."
    >
      {examples.map((example) => (
        <LanguageExamples
          key={example.title}
          title={example.title}
          description={example.description}
          examples={example.samples}
        />
      ))}
    </DocsLayout>
  );
}
