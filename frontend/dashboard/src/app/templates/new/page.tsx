import Link from "next/link";
import { FileText } from "lucide-react";
import { Button } from "@identitycore/ui";
import { EmptyState } from "@/components/shared/empty-state";
import { PageHeading } from "@/components/shared/page-heading";

export default function Page() {
  return (
    <div className="space-y-8">
      <PageHeading title="Create template" description="Templates are created from the live Templates page." />
      <EmptyState icon={FileText} title="Use the live create form" description="The Templates page creates real draft verification policies." />
      <Button asChild className="rounded-xl"><Link href="/templates">Open templates</Link></Button>
    </div>
  );
}
