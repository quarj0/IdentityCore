import Link from "next/link";
import { ScrollText } from "lucide-react";
import { Button } from "@identitycore/ui";
import { EmptyState } from "@/components/shared/empty-state";
import { PageHeading } from "@/components/shared/page-heading";

export default async function Page({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return (
    <div className="space-y-8">
      <PageHeading title="Audit event" description={`Event ID: ${id}`} />
      <EmptyState icon={ScrollText} title="Audit detail API is not available yet" description="Use the live Audit logs list to review tenant-scoped events." />
      <Button asChild className="rounded-xl"><Link href="/audit-logs">Back to audit logs</Link></Button>
    </div>
  );
}
