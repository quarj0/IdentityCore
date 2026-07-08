import {
  Button,
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Input,
  Label,
  Textarea,
} from "@identitycore/ui";

export function OrganizationSettingsForm() {
  return (
    <Card className="rounded-3xl border-slate-200 bg-white shadow-sm">
      <CardHeader>
        <CardTitle>Organization profile</CardTitle>
      </CardHeader>

      <CardContent>
        <form className="grid gap-5 sm:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="organizationName">Organization name</Label>
            <Input
              id="organizationName"
              defaultValue="Acme Financial Services"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="supportEmail">Support email</Label>
            <Input id="supportEmail" defaultValue="support@example.com" />
          </div>

          <div className="space-y-2 sm:col-span-2">
            <Label htmlFor="description">Use case</Label>
            <Textarea
              id="description"
              defaultValue="Identity workflows for onboarding and trust operations."
            />
          </div>

          <div className="sm:col-span-2">
            <Button type="button" className="rounded-xl">
              Save changes
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
