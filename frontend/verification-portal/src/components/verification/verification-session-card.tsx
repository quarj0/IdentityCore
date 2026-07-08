import { Clock, Mail, ShieldCheck } from "lucide-react";
import { mockSession } from "@/data/verification";

export function VerificationSessionCard() {
  return (
    <aside className="rounded-[2rem] border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex gap-3">
        <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-blue-50 text-blue-700 ring-1 ring-blue-100">
          <ShieldCheck className="h-5 w-5" aria-hidden="true" />
        </div>

        <div>
          <p className="text-sm font-semibold">
            {mockSession.organizationName}
          </p>
          <p className="mt-1 text-sm text-slate-600">
            {mockSession.workflowName}
          </p>
        </div>
      </div>

      <div className="mt-5 space-y-3 text-sm text-slate-600">
        <div className="flex items-center gap-2">
          <Clock className="h-4 w-4 text-blue-600" aria-hidden="true" />
          Expires in {mockSession.expiresIn}
        </div>

        <div className="flex items-center gap-2">
          <Mail className="h-4 w-4 text-blue-600" aria-hidden="true" />
          {mockSession.subjectEmail}
        </div>
      </div>
    </aside>
  );
}
