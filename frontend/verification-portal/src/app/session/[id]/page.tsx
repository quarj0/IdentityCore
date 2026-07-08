import { VerificationShell } from "@/components/layout/verification-shell";
import { VerificationFlow } from "@/components/verification/verification-flow";
import { VerificationHelpCard } from "@/components/verification/verification-help-card";
import { VerificationSessionCard } from "@/components/verification/verification-session-card";
import { mockSession } from "@/data/verification";

export default function VerificationSessionPage({
  params,
}: {
  params: { id: string };
}) {
  return (
    <VerificationShell>
      <div className="mb-6 rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
        <p className="text-sm font-medium text-blue-600">
          {mockSession.organizationName}
        </p>
        <h1 className="mt-1 text-2xl font-semibold tracking-tight">
          {mockSession.workflowName}
        </h1>
        <p className="mt-2 text-sm text-slate-600">Session: {params.id}</p>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1fr_320px]">
        <VerificationFlow />

        <div className="space-y-6">
          <VerificationSessionCard />
          <VerificationHelpCard />
        </div>
      </div>
    </VerificationShell>
  );
}
