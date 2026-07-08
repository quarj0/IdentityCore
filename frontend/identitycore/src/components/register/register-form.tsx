"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowRight, Building2, Loader2 } from "lucide-react";
import {
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  Input,
  Label,
  toast,
} from "@identitycore/ui";
import { AuthShell } from "@/components/auth/auth-shell";
import { OrganizationTypePicker } from "@/components/register/organization-type-picker";
import { getErrorMessage } from "@/lib/api-client";
import {
  fetchOrganizationOnboardingTypes,
  registerOrganizationOnboarding,
} from "@/lib/onboarding-api";

const TYPE_LABELS: Record<string, string> = {
  government: "Government",
  financial_institution: "Financial institution",
  educational_institution: "Educational institution",
  healthcare_provider: "Healthcare provider",
  enterprise: "Enterprise",
  ngo: "NGO",
  startup: "Startup",
  other: "Other",
};

export function RegisterForm() {
  const router = useRouter();
  const [submitting, setSubmitting] = useState(false);
  const [organizationTypes, setOrganizationTypes] = useState<string[]>([]);
  const [form, setForm] = useState({
    fullName: "",
    businessEmail: "",
    password: "",
    organizationName: "",
    organizationType: "",
    country: "",
    organizationCountry: "",
    website: "",
    supportEmail: "",
    phoneNumber: "",
  });

  useEffect(() => {
    fetchOrganizationOnboardingTypes()
      .then(setOrganizationTypes)
      .catch(() => {
        setOrganizationTypes([]);
      });
  }, []);

  const isKnownType = useMemo(
    () => organizationTypes.includes(form.organizationType),
    [form.organizationType, organizationTypes],
  );

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);

    try {
      const payload = await registerOrganizationOnboarding({
        fullName: form.fullName,
        businessEmail: form.businessEmail,
        password: form.password,
        country: form.country,
        organizationName: form.organizationName,
        organizationType: form.organizationType,
        organizationCountry: form.organizationCountry || form.country,
        website: form.website,
        supportEmail: form.supportEmail,
        phoneNumber: form.phoneNumber,
      });

      const verificationUrl = payload.debugEmailVerificationUrl;
      const token = verificationUrl
        ? new URL(verificationUrl).searchParams.get("token")
        : null;

      if (token) {
        router.push(`/verify-email?token=${encodeURIComponent(token)}`);
        return;
      }

      router.push(
        `/verify-email?email=${encodeURIComponent(form.businessEmail)}`,
      );
    } catch (error) {
      toast({
        title: "Registration failed",
        description: getErrorMessage(error),
        variant: "destructive",
      });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AuthShell
      badge="Create workspace"
      title="Register your organization and start in sandbox."
      description="Create an administrator account and organization workspace together. Production access is unlocked after verification and approval."
    >
      <Card className="w-full rounded-[2rem] border-slate-200/80 bg-white/90 shadow-[0_24px_80px_rgba(15,23,42,0.12)] backdrop-blur">
        <CardHeader>
          <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-blue-50 text-blue-700 ring-1 ring-blue-100">
            <Building2 className="h-5 w-5" aria-hidden="true" />
          </div>
          <CardTitle>Create organization workspace</CardTitle>
          <CardDescription>
            You will verify your email before continuing onboarding.
          </CardDescription>
        </CardHeader>

        <CardContent>
          <form className="space-y-8" onSubmit={handleSubmit}>
            <section>
              <p className="text-sm font-semibold">Administrator</p>

              <div className="mt-4 grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="fullName">Full name</Label>
                  <Input
                    id="fullName"
                    autoComplete="name"
                    placeholder="Kwadwo Owusu Ansah"
                    value={form.fullName}
                    onChange={(event) =>
                      setForm((current) => ({
                        ...current,
                        fullName: event.target.value,
                      }))
                    }
                    required
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="email">Business email</Label>
                  <Input
                    id="email"
                    type="email"
                    autoComplete="email"
                    placeholder="you@company.com"
                    value={form.businessEmail}
                    onChange={(event) =>
                      setForm((current) => ({
                        ...current,
                        businessEmail: event.target.value,
                      }))
                    }
                    required
                  />
                </div>

                <div className="space-y-2 sm:col-span-2">
                  <Label htmlFor="password">Password</Label>
                  <Input
                    id="password"
                    type="password"
                    autoComplete="new-password"
                    value={form.password}
                    onChange={(event) =>
                      setForm((current) => ({
                        ...current,
                        password: event.target.value,
                      }))
                    }
                    required
                  />
                </div>
              </div>
            </section>

            <section>
              <p className="text-sm font-semibold">Organization</p>

              <div className="mt-4 grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="organizationName">Organization name</Label>
                  <Input
                    id="organizationName"
                    placeholder="Acme Financial Services"
                    value={form.organizationName}
                    onChange={(event) =>
                      setForm((current) => ({
                        ...current,
                        organizationName: event.target.value,
                      }))
                    }
                    required
                  />
                </div>

                <div className="space-y-2 sm:col-span-2">
                  <OrganizationTypePicker
                    value={form.organizationType}
                    onChange={(organizationType) =>
                      setForm((current) => ({
                        ...current,
                        organizationType,
                      }))
                    }
                  />
                  {form.organizationType && !isKnownType ? (
                    <p className="text-xs text-red-600">
                      This organization type is not currently enabled by the
                      platform. Please contact support for assistance.
                    </p>
                  ) : null}
                  {organizationTypes.length ? (
                    <p className="text-xs text-muted-foreground">
                      Available types:{" "}
                      {organizationTypes
                        .map((type) => TYPE_LABELS[type] ?? type)
                        .join(", ")}
                    </p>
                  ) : null}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="country">Administrator country</Label>
                  <Input
                    id="country"
                    autoComplete="country-name"
                    placeholder="Ghana"
                    value={form.country}
                    onChange={(event) =>
                      setForm((current) => ({
                        ...current,
                        country: event.target.value,
                        organizationCountry:
                          current.organizationCountry || event.target.value,
                      }))
                    }
                    required
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="organizationCountry">
                    Organization country
                  </Label>
                  <Input
                    id="organizationCountry"
                    autoComplete="country-name"
                    placeholder="Ghana"
                    value={form.organizationCountry}
                    onChange={(event) =>
                      setForm((current) => ({
                        ...current,
                        organizationCountry: event.target.value,
                      }))
                    }
                    required
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="website">Website</Label>
                  <Input
                    id="website"
                    type="url"
                    autoComplete="url"
                    placeholder="https://company.com"
                    value={form.website}
                    onChange={(event) =>
                      setForm((current) => ({
                        ...current,
                        website: event.target.value,
                      }))
                    }
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="supportEmail">Support email</Label>
                  <Input
                    id="supportEmail"
                    type="email"
                    placeholder="support@company.com"
                    value={form.supportEmail}
                    onChange={(event) =>
                      setForm((current) => ({
                        ...current,
                        supportEmail: event.target.value,
                      }))
                    }
                    required
                  />
                </div>

                <div className="space-y-2 sm:col-span-2">
                  <Label htmlFor="phone">Phone number</Label>
                  <Input
                    id="phone"
                    type="tel"
                    autoComplete="tel"
                    placeholder="+233..."
                    value={form.phoneNumber}
                    onChange={(event) =>
                      setForm((current) => ({
                        ...current,
                        phoneNumber: event.target.value,
                      }))
                    }
                    required
                  />
                </div>
              </div>
            </section>

            <Button
              type="submit"
              size="lg"
              className="w-full rounded-xl"
              disabled={submitting || !form.organizationType || !isKnownType}
            >
              {submitting ? (
                <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
              ) : (
                <ArrowRight className="h-4 w-4" aria-hidden="true" />
              )}
              Create workspace
            </Button>

            <p className="text-center text-sm text-muted-foreground">
              Already have a workspace?{" "}
              <Link href="/login" className="font-medium text-blue-600">
                Sign in
              </Link>
            </p>
          </form>
        </CardContent>
      </Card>
    </AuthShell>
  );
}
