import Link from "next/link";
import { Webhook } from "lucide-react";
import { Button } from "@identitycore/ui";
import { EmptyState } from "@/components/shared/empty-state";
import { PageHeading } from "@/components/shared/page-heading";

export default function Page() {
  return (
    <div className="space-y-8">
      <PageHeading title="Add webhook" description="Webhook endpoints are created on the live webhooks page." />
      <EmptyState icon={Webhook} title="Use the live create form" description="The webhooks page creates real endpoints and shows the one-time signing secret." />
      <Button asChild className="rounded-xl"><Link href="/webhooks">Open webhooks</Link></Button>
    </div>
  );
}
