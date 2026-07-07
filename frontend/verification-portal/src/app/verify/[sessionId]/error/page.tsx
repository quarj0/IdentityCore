import Link from "next/link";
import { Button } from "@identitycore/ui";
import { SessionStatePage } from "@/components/session-state-page";

export default async function VerificationErrorPage({
  params,
}: {
  params: Promise<{ sessionId: string }>;
}) {
  const { sessionId } = await params;

  return (
    <div className="space-y-4">
      <SessionStatePage
        title="We could not complete this verification step"
        description="A recoverable upload or capture issue interrupted the session. You can retry the flow or return later with a fresh link."
        badge={`Session ${sessionId}`}
        icon="error"
        primaryHref={`/verify/${sessionId}`}
        primaryLabel="Retry session"
      />
      <div className="-mt-20 flex justify-center">
        <Button variant="outline" asChild>
          <Link href="/">Back to portal root</Link>
        </Button>
      </div>
    </div>
  );
}
