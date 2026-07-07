import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { ArrowLeft, Copy, ExternalLink } from "lucide-react";
import { Badge, Button, Card, CardContent, CardDescription, CardHeader, CardTitle, PageHeader } from "@identitycore/ui";
import { getStatusBadgeVariant, verificationRequests } from "@/lib/mock-data";

export const metadata: Metadata = { title: "Verification Request Detail" };

export default async function VerificationRequestDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const request = verificationRequests.find((item) => item.id === id);

  if (!request) notFound();

  return (
    <div className="space-y-6">
      <PageHeader
        title={request.subject}
        description={`Verification request ${request.id} for ${request.policy}.`}
        actions={
          <>
            <Button variant="outline" asChild>
              <Link href="/verifications/requests">
                <ArrowLeft className="h-4 w-4" />
                Back to requests
              </Link>
            </Button>
            <Button><Copy className="h-4 w-4" />Copy link</Button>
          </>
        }
      />

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1.15fr)_minmax(0,0.85fr)]">
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-base">Lifecycle</CardTitle>
                <CardDescription>Current request state and decision context.</CardDescription>
              </div>
              <Badge variant={getStatusBadgeVariant(request.status)}>{request.status}</Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-4 text-sm">
            <div className="rounded-lg border border-border p-4">
              <div className="font-medium text-foreground">Decision summary</div>
              <p className="mt-2 leading-6 text-muted-foreground">{request.decision}</p>
            </div>
            <div className="grid gap-3 md:grid-cols-2">
              <div className="rounded-lg bg-muted/50 p-4">
                <div className="text-xs uppercase tracking-wider text-muted-foreground">Created</div>
                <div className="mt-1 font-medium text-foreground">{request.created}</div>
              </div>
              <div className="rounded-lg bg-muted/50 p-4">
                <div className="text-xs uppercase tracking-wider text-muted-foreground">Expires</div>
                <div className="mt-1 font-medium text-foreground">{request.expires}</div>
              </div>
            </div>
            <div className="rounded-lg border border-border p-4">
              <div className="font-medium text-foreground">Hosted session URL</div>
              <code className="mt-2 block rounded bg-muted px-3 py-2 text-xs">{request.link}</code>
            </div>
          </CardContent>
        </Card>

        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Relationships</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              <Button variant="outline" className="w-full justify-between" asChild>
                <Link href={`/verifications/subjects/${request.subjectId}`}>
                  Open subject
                  <ExternalLink className="h-4 w-4" />
                </Link>
              </Button>
              <Button variant="outline" className="w-full justify-between" asChild>
                <Link href={`/verifications/policies/${request.policyId}`}>
                  Open policy
                  <ExternalLink className="h-4 w-4" />
                </Link>
              </Button>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Evidence checklist</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm text-muted-foreground">
              <div>Document capture received</div>
              <div>Selfie capture received</div>
              <div>Decision written to audit trail</div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
