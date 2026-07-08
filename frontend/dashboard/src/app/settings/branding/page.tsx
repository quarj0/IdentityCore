import { Paintbrush } from "lucide-react";
import { EmptyState } from "@/components/shared/empty-state";
import { PageHeading } from "@/components/shared/page-heading";

export default function Page() {
  return (
    <div className="space-y-8">
      <PageHeading
        title="Branding"
        description="Customize hosted verification branding."
      />
      <EmptyState
        icon={Paintbrush}
        title="Branding controls ready"
        description="Upload logos, set colors, and configure hosted verification appearance later."
      />
    </div>
  );
}
