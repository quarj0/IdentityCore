import Link from "next/link";
import { KeyRound } from "lucide-react";
import { Button } from "@identitycore/ui";
import { EmptyState } from "@/components/shared/empty-state";
import { PageHeading } from "@/components/shared/page-heading";

export default function Page() {
  return (
    <div className="space-y-8">
      <PageHeading title="Create API key" description="API keys are created on the live API keys page." />
      <EmptyState icon={KeyRound} title="Use the live create form" description="The API keys page creates real credentials and shows the one-time secret." />
      <Button asChild className="rounded-xl"><Link href="/api-keys">Open API keys</Link></Button>
    </div>
  );
}
