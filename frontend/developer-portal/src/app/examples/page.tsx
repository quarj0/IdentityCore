import { CodeBlock } from "@/components/docs/code-block";
import { DocsLayout } from "@/components/docs/docs-layout";
import { examples } from "@/data/examples";

export default function ExamplesPage() {
  return (
    <DocsLayout
      title="Examples"
      description="Common API and webhook examples for integrating IdentityCore into your product."
    >
      {examples.map((example) => (
        <CodeBlock key={example.title} {...example} />
      ))}
    </DocsLayout>
  );
}
