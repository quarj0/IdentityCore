import { ShieldCheck } from "lucide-react";
import { EmptyState } from "@/components/shared/empty-state";
import { PageHeading } from "@/components/shared/page-heading";

export default function Page() {
  return (
    <div className="space-y-8">
      <PageHeading
        title="Security settings"
        description="Configure MFA, sessions, and security controls."
      />
      <EmptyState
        icon={ShieldCheck}
        title="Security settings ready"
        description="Security settings will connect to authentication and organization APIs."
      />
    </div>
  );
}
