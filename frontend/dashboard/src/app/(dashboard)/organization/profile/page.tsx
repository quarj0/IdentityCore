import type { Metadata } from "next";
import { Badge, Button, Card, CardContent, CardDescription, CardHeader, CardTitle, Input, Label, PageHeader, Textarea } from "@identitycore/ui";

export const metadata: Metadata = { title: "Organization Profile" };

export default function OrganizationProfilePage() {
  return (
    <div className="max-w-5xl space-y-6">
      <PageHeader
        title="Organization profile"
        description="Maintain the legal, operational, and support information used across verification flows."
        actions={<Button>Save profile</Button>}
      />

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1.2fr)_minmax(0,0.8fr)]">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Legal identity</CardTitle>
            <CardDescription>Core organization records used for onboarding and trust reviews.</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="org-legal-name">Legal name</Label>
              <Input id="org-legal-name" defaultValue="Acme Corporation" />
            </div>
            <div className="space-y-2">
              <Label htmlFor="org-country">Country of registration</Label>
              <Input id="org-country" defaultValue="Ghana" />
            </div>
            <div className="space-y-2">
              <Label htmlFor="org-reg-no">Registration number</Label>
              <Input id="org-reg-no" defaultValue="CS123456789" />
            </div>
            <div className="space-y-2">
              <Label htmlFor="org-tax-id">Tax ID</Label>
              <Input id="org-tax-id" defaultValue="TIN-4481132" />
            </div>
            <div className="space-y-2 md:col-span-2">
              <Label htmlFor="org-address">Registered address</Label>
              <Textarea id="org-address" defaultValue="4 Ridge Towers, Independence Avenue, Accra, Ghana" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-base">Approval posture</CardTitle>
                <CardDescription>Signals used by operations during production review.</CardDescription>
              </div>
              <Badge variant="warning">Pending review</Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-4 text-sm">
            <div className="rounded-lg border border-border p-4">
              <div className="font-medium text-foreground">Support contact</div>
              <div className="mt-1 text-muted-foreground">support@acme.com</div>
            </div>
            <div className="rounded-lg border border-border p-4">
              <div className="font-medium text-foreground">Operational owner</div>
              <div className="mt-1 text-muted-foreground">Alex Carter, Head of Trust Operations</div>
            </div>
            <div className="rounded-lg border border-border p-4">
              <div className="font-medium text-foreground">Use case summary</div>
              <div className="mt-1 text-muted-foreground">
                Customer onboarding for regulated financial-product access across West Africa.
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
