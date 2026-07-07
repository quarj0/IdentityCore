import type { Metadata } from "next";
import { Copy, Send } from "lucide-react";
import { Button, Card, CardContent, CardDescription, CardHeader, CardTitle, Input, Label, PageHeader, Select, SelectContent, SelectItem, SelectTrigger, SelectValue, Textarea } from "@identitycore/ui";
import { verificationPolicies } from "@/lib/mock-data";

export const metadata: Metadata = { title: "Create Verification" };

export default function CreateVerificationPage() {
  return (
    <div className="max-w-5xl space-y-6">
      <PageHeader
        title="Create verification"
        description="Launch a no-code verification request and generate a secure subject link."
        actions={
          <>
            <Button variant="outline"><Copy className="h-4 w-4" />Copy sample payload</Button>
            <Button><Send className="h-4 w-4" />Generate link</Button>
          </>
        }
      />

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1.3fr)_minmax(0,0.7fr)]">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Request details</CardTitle>
            <CardDescription>Everything needed to create a hosted verification session.</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="subject-name">Subject name</Label>
              <Input id="subject-name" defaultValue="Ama Ofori" />
            </div>
            <div className="space-y-2">
              <Label htmlFor="subject-email">Email address</Label>
              <Input id="subject-email" type="email" defaultValue="ama.ofori@example.com" />
            </div>
            <div className="space-y-2">
              <Label htmlFor="project">Project</Label>
              <Select defaultValue="proj-core-onboarding">
                <SelectTrigger id="project">
                  <SelectValue placeholder="Select project" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="proj-core-onboarding">Core onboarding</SelectItem>
                  <SelectItem value="proj-sandbox-labs">Sandbox labs</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="policy">Verification policy</Label>
              <Select defaultValue={verificationPolicies[0].id}>
                <SelectTrigger id="policy">
                  <SelectValue placeholder="Select policy" />
                </SelectTrigger>
                <SelectContent>
                  {verificationPolicies.map((policy) => (
                    <SelectItem key={policy.id} value={policy.id}>{policy.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2 md:col-span-2">
              <Label htmlFor="purpose">Purpose</Label>
              <Textarea id="purpose" defaultValue="Customer onboarding for regulated account opening." />
            </div>
            <div className="space-y-2 md:col-span-2">
              <Label htmlFor="metadata">Internal metadata</Label>
              <Textarea id="metadata" defaultValue='{"customer_id":"cus_2911","journey":"retail-account-opening"}' />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Generated outcome</CardTitle>
            <CardDescription>What the no-code flow will produce when submitted.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4 text-sm">
            <div className="rounded-lg border border-border p-4">
              <div className="font-medium text-foreground">Verification link</div>
              <code className="mt-2 block rounded bg-muted px-3 py-2 text-xs">https://verify.identitycore.com/verify/sess_demo_2419</code>
            </div>
            <div className="rounded-lg border border-border p-4">
              <div className="font-medium text-foreground">Expected webhooks</div>
              <div className="mt-2 text-muted-foreground">
                `verification.created`, `verification.submitted`, `verification.completed`
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
