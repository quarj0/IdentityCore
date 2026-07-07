import { FileUp, ShieldCheck } from "lucide-react";
import {
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@identitycore/ui";
import { OnboardingPageShell } from "@/components/onboarding/onboarding-page-shell";

export default function OrganizationVerificationPage() {
  return (
    <OnboardingPageShell
      eyebrow="Organization verification"
      title="Verify your organization."
      description="Upload documents that prove your organization is legitimate before production access is approved."
      pathname="/onboarding/organization-verification"
    >
      <div className="grid gap-6 md:grid-cols-2">
        {[
          [
            "Business registration certificate",
            "Certificate of incorporation, registration certificate, or equivalent.",
          ],
          [
            "Operating license",
            "Required for regulated organizations such as finance, healthcare, telecom, or government.",
          ],
        ].map(([title, description]) => (
          <Card
            key={title}
            className="rounded-3xl border-slate-200 bg-white p-2 shadow-sm"
          >
            <CardHeader>
              <FileUp className="mb-4 h-6 w-6 text-blue-600" />
              <CardTitle>{title}</CardTitle>
              <CardDescription className="leading-7">
                {description}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button
                type="button"
                variant="outline"
                size="lg"
                className="w-full rounded-xl"
              >
                Upload document
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="mt-6 rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="flex gap-3">
          <ShieldCheck className="mt-1 h-5 w-5 text-blue-600" />
          <p className="text-sm leading-7 text-muted-foreground">
            Documents remain private and are reviewed only for organization
            approval.
          </p>
        </div>
      </div>
    </OnboardingPageShell>
  );
}
