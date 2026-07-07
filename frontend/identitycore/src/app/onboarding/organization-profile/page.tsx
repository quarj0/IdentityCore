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
import { OnboardingPageShell } from "@/components/onboarding/onboarding-page-shell";

export default function OrganizationProfilePage() {
  return (
    <OnboardingPageShell
      eyebrow="Organization profile"
      title="Tell us about your organization."
      description="This information helps IdentityCore understand who owns the workspace and how your organization will use identity infrastructure."
      pathname="/onboarding/organization-profile"
    >
      <Card className="rounded-3xl border-slate-200 bg-white p-2 shadow-sm">
        <CardHeader>
          <CardTitle>Organization details</CardTitle>
        </CardHeader>

        <CardContent>
          <form className="grid gap-5 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="legalName">Legal organization name</Label>
              <Input id="legalName" placeholder="Acme Financial Services Ltd" />
            </div>

            <div className="space-y-2">
              <Label htmlFor="registrationNumber">Registration number</Label>
              <Input id="registrationNumber" placeholder="CS123456789" />
            </div>

            <div className="space-y-2">
              <Label htmlFor="country">Country</Label>
              <Input id="country" placeholder="Ghana" />
            </div>

            <div className="space-y-2">
              <Label htmlFor="website">Official website</Label>
              <Input
                id="website"
                type="url"
                placeholder="https://company.com"
              />
            </div>

            <div className="space-y-2 sm:col-span-2">
              <Label htmlFor="address">Registered address</Label>
              <Textarea
                id="address"
                placeholder="Organization registered address"
              />
            </div>

            <div className="space-y-2 sm:col-span-2">
              <Label htmlFor="useCase">Primary use case</Label>
              <Textarea
                id="useCase"
                placeholder="Tell us how your organization plans to use IdentityCore."
              />
            </div>

            <div className="sm:col-span-2">
              <Button type="button" size="lg" className="w-full rounded-xl sm:w-auto">
                Save and continue
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </OnboardingPageShell>
  );
}
