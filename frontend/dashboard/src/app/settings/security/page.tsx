import { OwnedSessions } from "@/components/auth/owned-sessions";
import Link from "next/link";
import { Button, Card, CardContent } from "@identitycore/ui";
import { SettingsNavigation } from "@/components/shared/settings-navigation";
import { PageHeading } from "@/components/shared/page-heading";
export default function Page() {
  const home =
    process.env.NEXT_PUBLIC_IDENTITYCORE_ORIGIN ?? "http://localhost:3001";
  return (
    <div className="space-y-8">
      <PageHeading
        title="Security settings"
        description="Manage account credentials and review workspace security controls."
      />
      <SettingsNavigation />
      <Card>
        <CardContent className="space-y-4 p-6">
          <h2 className="font-semibold">Password</h2>
          <p className="text-sm text-slate-600">
            Change your password through the shared IdentityCore account flow.
            Changing your password signs out every device. Sign in again with
            your new password.
          </p>
          <Button asChild>
            <Link href={`${home}/change-password`}>Change password</Link>
          </Button>
        </CardContent>
      </Card>
      <OwnedSessions />
      <Card>
        <CardContent className="space-y-2 p-6">
          <h2 className="font-semibold">Workspace security</h2>
          <p className="text-sm text-slate-600">
            API credential rotation is available under API keys. Webhook signing
            and endpoint controls are available under Webhooks. Workspace
            suspension is available in Danger zone.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
