import Link from "next/link";
import { Send } from "lucide-react";
import { Button } from "@identitycore/ui";
import { CapturePanel } from "./capture-panel";

export function SubmittedStep() {
  return (
    <CapturePanel
      title="Verification submitted"
      description="Your verification result has been submitted to the requesting organization."
    >
      <div className="rounded-[2rem] border border-blue-100 bg-blue-50 p-6 text-center">
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-white text-blue-700 ring-1 ring-blue-100">
          <Send className="h-6 w-6" aria-hidden="true" />
        </div>

        <h2 className="mt-5 text-2xl font-semibold tracking-tight text-blue-950">
          You are done
        </h2>

        <p className="mx-auto mt-2 max-w-md text-sm leading-7 text-blue-800">
          Your verification will be reviewed and you will be notified of the
          result. You can close this session now.
        </p>

        <Button asChild className="mt-6 rounded-xl">
          <Link href="/completed">Close session</Link>
        </Button>
      </div>
    </CapturePanel>
  );
}
