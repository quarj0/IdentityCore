"use client";

import { useEffect, useMemo, useState } from "react";
import { CheckCircle2, Loader2, ShieldCheck, UserRound } from "lucide-react";
import {
  Button,
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
  Input,
  Label,
  Skeleton,
} from "@identitycore/ui";
import { PageHeading } from "@/components/shared/page-heading";
import { SettingsNavigation } from "@/components/shared/settings-navigation";
import { dashboardApi, DashboardUser } from "@/lib/dashboard-api";

export function LiveProfilePage() {
  const [user, setUser] = useState<DashboardUser | null>(null);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    dashboardApi
      .profile()
      .then((response) => setUser(response.user))
      .catch((caught: unknown) =>
        setError(
          caught instanceof Error
            ? caught.message
            : "Unable to load your profile.",
        ),
      );
  }, []);

  const initials = useMemo(() => {
    if (!user) return "";
    return (
      `${user.first_name.charAt(0)}${user.last_name.charAt(0)}`.toUpperCase() ||
      user.email.charAt(0).toUpperCase()
    );
  }, [user]);

  function update(
    field: "first_name" | "last_name" | "phone_number",
    value: string,
  ) {
    setUser((current) => (current ? { ...current, [field]: value } : current));
    setMessage("");
  }

  async function save(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!user || saving) return;
    setSaving(true);
    setMessage("");
    setError("");
    try {
      const response = await dashboardApi.updateProfile({
        first_name: user.first_name,
        last_name: user.last_name,
        phone_number: user.phone_number,
      });
      setUser(response.user);
      setMessage("Your profile has been updated.");
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Unable to save your changes.",
      );
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="mx-auto max-w-5xl space-y-7">
      <PageHeading
        title="Account settings"
        description="Manage your personal details and how you appear across this workspace."
      />
      <SettingsNavigation />

      {error ? (
        <div
          role="alert"
          className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
        >
          {error}
        </div>
      ) : null}
      {message ? (
        <div
          role="status"
          className="flex items-center gap-2 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800"
        >
          <CheckCircle2 className="h-4 w-4" /> {message}
        </div>
      ) : null}

      {!user && !error ? (
        <Card className="overflow-hidden rounded-2xl border-slate-200">
          <CardHeader className="border-b border-slate-100">
            <Skeleton className="h-6 w-40" />
            <Skeleton className="h-4 w-72" />
          </CardHeader>
          <CardContent className="grid gap-5 p-6 sm:grid-cols-2">
            {Array.from({ length: 4 }).map((_, index) => (
              <Skeleton key={index} className="h-14 w-full" />
            ))}
          </CardContent>
        </Card>
      ) : user ? (
        <form onSubmit={save}>
          <Card className="overflow-hidden rounded-2xl border-slate-200 shadow-sm">
            <CardHeader className="border-b border-slate-100 bg-slate-50/60 sm:flex-row sm:items-center sm:justify-between sm:space-y-0">
              <div>
                <CardTitle>Personal information</CardTitle>
                <CardDescription className="mt-1">
                  Keep your contact details accurate and up to date.
                </CardDescription>
              </div>
              <div
                className="mt-4 flex h-12 w-12 items-center justify-center rounded-full bg-slate-900 text-sm font-semibold text-white sm:mt-0"
                aria-label={`Initials ${initials}`}
              >
                {initials || <UserRound className="h-5 w-5" />}
              </div>
            </CardHeader>
            <CardContent className="grid gap-x-6 gap-y-5 p-6 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="first-name">First name</Label>
                <Input
                  id="first-name"
                  autoComplete="given-name"
                  value={user.first_name}
                  onChange={(event) => update("first_name", event.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="last-name">Last name</Label>
                <Input
                  id="last-name"
                  autoComplete="family-name"
                  value={user.last_name}
                  onChange={(event) => update("last_name", event.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="email">Email address</Label>
                <Input id="email" type="email" value={user.email} disabled />
                <p className="text-xs text-slate-500">
                  Contact an administrator to change your sign-in email.
                </p>
              </div>
              <div className="space-y-2">
                <Label htmlFor="phone-number">Phone number</Label>
                <Input
                  id="phone-number"
                  type="tel"
                  autoComplete="tel"
                  value={user.phone_number}
                  onChange={(event) =>
                    update("phone_number", event.target.value)
                  }
                  placeholder="Add a phone number"
                />
              </div>
            </CardContent>
            <CardFooter className="flex-col gap-3 border-t border-slate-100 bg-slate-50/60 px-6 py-4 sm:flex-row sm:justify-between">
              <div className="flex items-center gap-2 text-xs text-slate-500">
                <ShieldCheck className="h-4 w-4 text-emerald-600" /> Your
                account details are protected.
              </div>
              <Button
                type="submit"
                disabled={saving}
                className="w-full sm:w-auto"
              >
                {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
                {saving ? "Saving changes" : "Save changes"}
              </Button>
            </CardFooter>
          </Card>
        </form>
      ) : null}
    </div>
  );
}
