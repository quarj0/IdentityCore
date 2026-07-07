import type { Metadata } from "next";
import { Button, Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle, Input, Label, Separator } from "@identitycore/ui";

export const metadata: Metadata = { title: "Organization Settings" };

export default function SettingsPage() {
  return (
    <div className="p-6 space-y-6 max-w-4xl">
      <div>
        <h1 className="text-xl font-semibold tracking-tight">Organization Settings</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Configure your organization details, verification settings, and security policies.
        </p>
      </div>

      <div className="space-y-6">
        {/* Profile Details */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Profile Details</CardTitle>
            <CardDescription>Update your company name, brand details, and public profile info.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-2 sm:grid-cols-2">
              <div className="space-y-1">
                <Label htmlFor="company-name">Company Name</Label>
                <Input id="company-name" defaultValue="Acme Corporation" />
              </div>
              <div className="space-y-1">
                <Label htmlFor="company-slug">Organization ID / URL Slug</Label>
                <Input id="company-slug" defaultValue="acme" />
              </div>
            </div>
            <div className="grid gap-2 sm:grid-cols-2">
              <div className="space-y-1">
                <Label htmlFor="support-email">Support Email</Label>
                <Input id="support-email" type="email" defaultValue="support@acme.com" />
              </div>
              <div className="space-y-1">
                <Label htmlFor="website">Website</Label>
                <Input id="website" type="url" defaultValue="https://acme.com" />
              </div>
            </div>
          </CardContent>
          <CardFooter className="border-t border-border pt-4 justify-end">
            <Button size="sm" id="save-profile">Save Changes</Button>
          </CardFooter>
        </Card>

        {/* Security & Access Policies */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Security Policy</CardTitle>
            <CardDescription>Define access controls and session parameters for your organization.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm font-medium text-foreground">Require Multi-Factor Authentication</div>
                  <div className="text-xs text-muted-foreground">Force all team members to authenticate with MFA.</div>
                </div>
                <Button variant="outline" size="sm" id="toggle-mfa">Enable</Button>
              </div>
              <Separator />
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm font-medium text-foreground">Enforce IP Access Control</div>
                  <div className="text-xs text-muted-foreground">Restrict dashboard access to specific IP ranges.</div>
                </div>
                <Button variant="outline" size="sm" id="configure-ip">Configure</Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Danger zone */}
        <Card className="border-destructive/30 bg-destructive/5 dark:bg-destructive/10">
          <CardHeader>
            <CardTitle className="text-base text-destructive">Danger Zone</CardTitle>
            <CardDescription>Permanently delete this organization, all projects, policies and subjects. This cannot be undone.</CardDescription>
          </CardHeader>
          <CardFooter className="pt-0 justify-start">
            <Button variant="destructive" size="sm" id="delete-org">Delete Organization</Button>
          </CardFooter>
        </Card>
      </div>
    </div>
  );
}
