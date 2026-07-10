import { LiveVerificationFlow } from "@/components/verification/live-verification-flow";

export default async function VerificationSessionPage({
  params,
  searchParams,
}: {
  params: Promise<{ sessionId: string }>;
  searchParams: Promise<{ handoff?: string }>;
}) {
  const { sessionId } = await params;
  const { handoff } = await searchParams;
  return <LiveVerificationFlow sessionId={sessionId} handoff={handoff} />;
}
