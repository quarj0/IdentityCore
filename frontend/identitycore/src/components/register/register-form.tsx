"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  ArrowRight,
  Building2,
  CheckCircle2,
  Loader2,
} from "lucide-react";
import {
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  Input,
  Label,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@identitycore/ui";
import { AuthShell } from "@/components/auth/auth-shell";
import { PasswordInput } from "@/components/auth/password-input";
import { InlineStatus } from "@/components/feedback/inline-status";
import { OrganizationTypePicker } from "@/components/register/organization-type-picker";
import { getErrorMessage } from "@/lib/api-client";
import {
  getBusinessEmailValidationMessage,
  getPasswordValidationMessage,
  PASSWORD_REQUIREMENTS_MESSAGE,
} from "@/lib/registration-validation";
import {
  fetchOrganizationOnboardingTypes,
  registerOrganizationOnboarding,
} from "@/lib/onboarding-api";
import { fetchPublicCatalog } from "@/lib/public-graphql";

const STEPS = [
  { id: "account", label: "Account" },
  { id: "organization", label: "Organization" },
  { id: "contact", label: "Contact" },
] as const;

export function RegisterForm() {
  const router = useRouter();

  const [submitting, setSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [organizationTypes, setOrganizationTypes] = useState<string[]>([]);
  const [countries, setCountries] = useState<
    Array<{ code: string; name: string }>
  >([]);
  const [countriesLoading, setCountriesLoading] = useState(true);
  const [countriesError, setCountriesError] = useState(false);
  const [step, setStep] = useState(0);

  const [form, setForm] = useState({
    fullName: "",
    businessEmail: "",
    password: "",
    organizationName: "",
    organizationType: "",
    organizationCountry: "",
    website: "",
    supportEmail: "",
    phoneNumber: "",
  });

  useEffect(() => {
    void Promise.all([
      fetchOrganizationOnboardingTypes()
        .then(setOrganizationTypes)
        .catch(() => setOrganizationTypes([])),
      fetchPublicCatalog()
        .then((catalog) => {
          setCountries(catalog.countries);
          setCountriesError(false);
        })
        .catch(() => {
          setCountries([]);
          setCountriesError(true);
        })
        .finally(() => setCountriesLoading(false)),
    ]);
  }, []);

  const isKnownType = useMemo(
    () => organizationTypes.includes(form.organizationType),
    [form.organizationType, organizationTypes],
  );

  const businessEmailError = getBusinessEmailValidationMessage(
    form.businessEmail,
  );
  const passwordError = getPasswordValidationMessage(form.password);

  const canContinueAccountStep = Boolean(
    form.fullName.trim() &&
    form.businessEmail.trim() &&
    form.password.trim() &&
    !businessEmailError &&
    !passwordError,
  );

  const canContinueOrganizationStep = Boolean(
    form.organizationName.trim() &&
    form.organizationCountry.trim() &&
    form.organizationType &&
    isKnownType,
  );

  const canSubmitContactStep = Boolean(
    form.supportEmail.trim() && form.phoneNumber.trim(),
  );

  function goToStep(nextStep: number) {
    setErrorMessage(null);
    setStep(nextStep);
  }

  function handleNextStep() {
    if (step === 0 && !canContinueAccountStep) {
      setErrorMessage(
        businessEmailError ||
          passwordError ||
          "Complete the administrator details before continuing.",
      );
      return;
    }

    if (step === 1 && !canContinueOrganizationStep) {
      setErrorMessage("Complete the organization details before continuing.");
      return;
    }

    goToStep(step + 1);
  }

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!canSubmitContactStep) {
      setErrorMessage(
        "Complete the contact details before creating workspace.",
      );
      return;
    }

    setSubmitting(true);
    setErrorMessage(null);

    try {
      const payload = await registerOrganizationOnboarding({
        fullName: form.fullName,
        businessEmail: form.businessEmail,
        password: form.password,
        organizationName: form.organizationName,
        organizationType: form.organizationType,
        organizationCountry: form.organizationCountry,
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
      setErrorMessage(getErrorMessage(error));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AuthShell
      badge="Create workspace"
      title="Register your organization and start in sandbox."
      description="Create an administrator account and organization workspace. Production access is unlocked after verification and approval."
      sectionClassName="items-start lg:items-center"
    >
      <Card className="w-full max-w-xl rounded-4xl border-slate-200/80 bg-white/95 shadow-[0_24px_80px_rgba(15,23,42,0.12)] backdrop-blur">
        <CardHeader>
          <div className="mb-6 flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-blue-50 text-blue-700 ring-1 ring-blue-100">
              <Building2 className="h-5 w-5" aria-hidden="true" />
            </div>

            <div className="flex flex-1 items-center gap-2">
              {STEPS.map((item, index) => {
                const isActive = index === step;
                const isComplete = index < step;

                return (
                  <div
                    key={item.id}
                    className={`flex flex-1 items-center gap-2 rounded-full border px-3 py-2 text-xs font-medium ${
                      isActive
                        ? "border-blue-200 bg-blue-50 text-blue-700"
                        : isComplete
                          ? "border-emerald-200 bg-emerald-50 text-emerald-700"
                          : "border-slate-200 bg-white text-slate-500"
                    }`}
                  >
                    <span
                      className={`flex h-5 w-5 items-center justify-center rounded-full text-[11px] ${
                        isActive
                          ? "bg-blue-600 text-white"
                          : isComplete
                            ? "bg-emerald-600 text-white"
                            : "bg-slate-100 text-slate-500"
                      }`}
                    >
                      {isComplete ? (
                        <CheckCircle2 className="h-3.5 w-3.5" />
                      ) : (
                        index + 1
                      )}
                    </span>
                    <span className="hidden sm:inline">{item.label}</span>
                  </div>
                );
              })}
            </div>
          </div>

          <CardTitle>
            {step === 0 && "Create your administrator account"}
            {step === 1 && "Tell us about your organization"}
            {step === 2 && "Add contact information"}
          </CardTitle>

          <CardDescription>
            {step === 0 &&
              "Use a business email and secure password for the first organization administrator."}
            {step === 1 &&
              "Provide the basic organization details needed to create your workspace."}
            {step === 2 &&
              "Add contact details used for onboarding, verification updates, and support communication."}
          </CardDescription>
        </CardHeader>

        <CardContent>
          <form className="space-y-6" onSubmit={handleSubmit}>
            {errorMessage ? (
              <InlineStatus
                kind="error"
                title="Registration failed"
                message={errorMessage}
              />
            ) : null}

            {step === 0 ? (
              <section className="space-y-4">
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
                        supportEmail:
                          current.supportEmail || event.target.value,
                      }))
                    }
                    required
                  />
                  <p
                    className={`text-xs ${
                      businessEmailError
                        ? "text-red-600"
                        : "text-muted-foreground"
                    }`}
                  >
                    {businessEmailError ||
                      "Use a company-managed email address."}
                  </p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="password">Password</Label>
                  <PasswordInput
                    id="password"
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
                  <p
                    className={`text-xs ${
                      passwordError ? "text-red-600" : "text-muted-foreground"
                    }`}
                  >
                    {passwordError || PASSWORD_REQUIREMENTS_MESSAGE}
                  </p>
                </div>
              </section>
            ) : null}

            {step === 1 ? (
              <section className="space-y-4">
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
                    platform.
                  </p>
                ) : null}

                <div className="space-y-2">
                  <Label htmlFor="organizationCountry">
                    Organization country
                  </Label>
                  <Select
                    value={form.organizationCountry}
                    disabled={countriesLoading || countriesError}
                    onValueChange={(value) =>
                      setForm((current) => ({
                        ...current,
                        organizationCountry: value,
                      }))
                    }
                  >
                    <SelectTrigger id="organizationCountry">
                      <SelectValue
                        placeholder={
                          countriesLoading
                            ? "Loading countries..."
                            : "Select country"
                        }
                      />
                    </SelectTrigger>
                    <SelectContent>
                      {countries.map((country) => (
                        <SelectItem key={country.code} value={country.code}>
                          {country.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  {countriesError ? (
                    <p className="text-xs text-red-600">
                      Countries could not be loaded. Refresh the page to try
                      again.
                    </p>
                  ) : null}
                </div>
              </section>
            ) : null}

            {step === 2 ? (
              <section className="space-y-4">
                <div className="rounded-2xl border border-slate-200 bg-slate-50/80 p-4 text-sm leading-6 text-muted-foreground">
                  Sandbox access is available after email verification.
                  Production access is unlocked after organization review and
                  approval.
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

                <div className="space-y-2">
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
              </section>
            ) : null}

            <div className="flex flex-col gap-3 border-t border-slate-200 pt-6 sm:flex-row sm:items-center sm:justify-between">
              <p className="text-sm text-muted-foreground">
                Step {step + 1} of {STEPS.length}
              </p>

              <div className="flex flex-col gap-3 sm:flex-row">
                {step > 0 ? (
                  <Button
                    type="button"
                    variant="outline"
                    size="lg"
                    className="rounded-xl"
                    onClick={() => goToStep(step - 1)}
                  >
                    <ArrowLeft className="h-4 w-4" aria-hidden="true" />
                    Back
                  </Button>
                ) : null}

                {step < STEPS.length - 1 ? (
                  <Button
                    type="button"
                    size="lg"
                    className="rounded-xl"
                    onClick={handleNextStep}
                    disabled={
                      step === 0
                        ? !canContinueAccountStep
                        : !canContinueOrganizationStep
                    }
                  >
                    Continue
                    <ArrowRight className="h-4 w-4" aria-hidden="true" />
                  </Button>
                ) : (
                  <Button
                    type="submit"
                    size="lg"
                    className="rounded-xl"
                    disabled={submitting || !canSubmitContactStep}
                  >
                    {submitting ? (
                      <Loader2
                        className="h-4 w-4 animate-spin"
                        aria-hidden="true"
                      />
                    ) : (
                      <ArrowRight className="h-4 w-4" aria-hidden="true" />
                    )}
                    Create workspace
                  </Button>
                )}
              </div>
            </div>

            <p className="text-center text-sm text-muted-foreground">
              Already have an workspace?{" "}
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
