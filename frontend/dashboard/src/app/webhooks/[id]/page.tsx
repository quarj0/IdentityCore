import Link from "next/link";
import { Webhook } from "lucide-react";
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
      <PageHeading title="Webhook endpoint" description={`Webhook ID: ${id}`} />
      <EmptyState icon={Webhook} title="Webhook detail API is not available yet" description="Use the live Webhooks list to create and test endpoints." />
      <Button asChild className="rounded-xl"><Link href="/webhooks">Back to webhooks</Link></Button>
    </div>
  );
}
