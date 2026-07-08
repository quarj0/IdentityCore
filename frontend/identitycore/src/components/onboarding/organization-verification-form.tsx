"use client";

import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";
import {
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  Input,
  Label,
  Textarea,
  toast,
} from "@identitycore/ui";
import { getErrorMessage } from "@/lib/api-client";
import {
  fetchCurrentOnboarding,
  submitOrganizationVerification,
} from "@/lib/onboarding-api";

export function OrganizationVerificationForm() {
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [form, setForm] = useState({
    businessRegistrationNumber: "",
    registeredAddress: "",
    officialWebsite: "",
    taxIdentificationNumber: "",
  });

  useEffect(() => {
    fetchCurrentOnboarding()
      .then((state) => {
        setForm((current) => ({
          ...current,
          officialWebsite: state.website || "",
        }));
      })
      .catch((error) => {
        toast({
          title: "Unable to load onboarding state",
          description: getErrorMessage(error),
          variant: "destructive",
        });
      })
      .finally(() => setLoading(false));
  }, []);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);

    try {
      await submitOrganizationVerification({
        ...form,
        supportingDocumentKeys: [],
      });
      toast({
        title: "Organization details submitted",
        description:
          "Your onboarding record has been updated and the next step is ready.",
      });
    } catch (error) {
      toast({
        title: "Unable to submit organization details",
        description: getErrorMessage(error),
        variant: "destructive",
      });
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) {
    return (
      <div className="flex min-h-48 items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="grid gap-6 md:grid-cols-2">
      <Card className="rounded-3xl border-slate-200 bg-white p-2 shadow-sm md:col-span-2">
        <CardHeader>
          <CardTitle>Submit organization verification</CardTitle>
          <CardDescription className="leading-7">
            These details are stored in the onboarding record immediately. Public
            document upload endpoints are not available yet, so supporting files
            can be shared during review after this step is submitted.
          </CardDescription>
        </CardHeader>

        <CardContent>
          <form className="grid gap-5 sm:grid-cols-2" onSubmit={handleSubmit}>
            <div className="space-y-2">
              <Label htmlFor="businessRegistrationNumber">
                Business registration number
              </Label>
              <Input
                id="businessRegistrationNumber"
                value={form.businessRegistrationNumber}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    businessRegistrationNumber: event.target.value,
                  }))
                }
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="taxIdentificationNumber">
                Tax identification number
              </Label>
              <Input
                id="taxIdentificationNumber"
                value={form.taxIdentificationNumber}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    taxIdentificationNumber: event.target.value,
                  }))
                }
              />
            </div>

            <div className="space-y-2 sm:col-span-2">
              <Label htmlFor="officialWebsite">Official website</Label>
              <Input
                id="officialWebsite"
                type="url"
                value={form.officialWebsite}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    officialWebsite: event.target.value,
                  }))
                }
              />
            </div>

            <div className="space-y-2 sm:col-span-2">
              <Label htmlFor="registeredAddress">Registered address</Label>
              <Textarea
                id="registeredAddress"
                value={form.registeredAddress}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    registeredAddress: event.target.value,
                  }))
                }
                required
              />
            </div>

            <div className="sm:col-span-2">
              <Button
                type="submit"
                size="lg"
                className="w-full rounded-xl sm:w-auto"
                disabled={submitting}
              >
                {submitting ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : null}
                Save and continue
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
