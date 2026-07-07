import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { Badge, Button, Card, CardContent, CardDescription, CardHeader, CardTitle, Input, Label, PageHeader, Switch } from "@identitycore/ui";
import { verificationPolicies } from "@/lib/mock-data";

export const metadata: Metadata = { title: "Policy Detail" };

export default async function VerificationPolicyDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const policy = verificationPolicies.find((item) => item.id === id);

  if (!policy) notFound();

  return (
    <div className="max-w-5xl space-y-6">
      <PageHeader
        title={policy.name}
        description={policy.description}
        actions={
          <>
            <Badge variant={policy.active ? "success" : "secondary"}>{policy.active ? "Active" : "Inactive"}</Badge>
            <Button>Save policy</Button>
          </>
        }
      />

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1.1fr)_minmax(0,0.9fr)]">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Policy builder</CardTitle>
            <CardDescription>Configure the checks that control automated and manual decisions.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-5">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="face-threshold">Face match threshold</Label>
                <Input id="face-threshold" defaultValue={policy.faceMatchThreshold ?? ""} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="review-threshold">Manual review threshold</Label>
                <Input id="review-threshold" defaultValue={policy.manualReviewThreshold} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="expiry-days">Verification expiry (days)</Label>
                <Input id="expiry-days" defaultValue={policy.expiryDays} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="retention-days">Retention (days)</Label>
                <Input id="retention-days" defaultValue={policy.retentionDays} />
              </div>
            </div>
            <div className="space-y-3 rounded-lg border border-border p-4">
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-medium text-foreground">Require selfie</div>
                  <div className="text-sm text-muted-foreground">Capture a face photo for comparison.</div>
                </div>
                <Switch checked={policy.selfie} />
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-medium text-foreground">Require liveness</div>
                  <div className="text-sm text-muted-foreground">Challenge the subject to prove presence.</div>
                </div>
                <Switch checked={policy.liveness} />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Accepted documents</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {policy.docTypes.map((type) => (
              <div key={type} className="rounded-lg border border-border px-4 py-3 text-sm font-medium text-foreground">
                {type}
              </div>
            ))}
            <div className="rounded-lg bg-muted/50 p-4 text-sm text-muted-foreground">
              Used {policy.usageCount.toLocaleString()} times across current projects.
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
