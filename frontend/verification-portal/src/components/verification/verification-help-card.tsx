import { HelpCircle } from "lucide-react";

export function VerificationHelpCard() {
  return (
    <aside className="rounded-[2rem] border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex gap-3">
        <HelpCircle className="mt-1 h-5 w-5 text-blue-600" aria-hidden="true" />
        <div>
          <p className="text-sm font-semibold">Need help?</p>
          <p className="mt-2 text-sm leading-6 text-slate-600">
            Use a clear document, avoid glare, and make sure your face is
            visible during selfie and liveness capture.
          </p>
        </div>
      </div>
    </aside>
  );
}
