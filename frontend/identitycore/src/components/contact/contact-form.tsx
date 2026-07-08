"use client";

import { useState } from "react";
import Link from "next/link";
import { ArrowRight, Loader2, Mail } from "lucide-react";
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
  Textarea,
  toast,
} from "@identitycore/ui";
import { getErrorMessage } from "@/lib/api-client";
import { submitContactInquiry } from "@/lib/public-graphql";

export function ContactForm() {
  const [submitting, setSubmitting] = useState(false);
  const [interest, setInterest] = useState("");
  const [form, setForm] = useState({
    fullName: "",
    businessEmail: "",
    organizationName: "",
    message: "",
  });

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);

    try {
      const payload = await submitContactInquiry({
        ...form,
        interest,
      });
      toast({
        title: "Message sent",
        description: payload.message,
      });
      setForm({
        fullName: "",
        businessEmail: "",
        organizationName: "",
        message: "",
      });
      setInterest("");
    } catch (error) {
      toast({
        title: "Unable to send message",
        description: getErrorMessage(error),
        variant: "destructive",
      });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Card className="rounded-[2rem] border-slate-200/80 bg-white/90 shadow-[0_24px_80px_rgba(15,23,42,0.12)] backdrop-blur">
      <CardHeader>
        <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-blue-50 text-blue-700 ring-1 ring-blue-100">
          <Mail className="h-5 w-5" />
        </div>
        <CardTitle>Send a message</CardTitle>
        <CardDescription>
          Submit your inquiry directly from IdentityCore and our team can follow
          up from the review queue.
        </CardDescription>
      </CardHeader>

      <CardContent>
        <form className="grid gap-5 sm:grid-cols-2" onSubmit={handleSubmit}>
          <div className="space-y-2">
            <Label htmlFor="fullName">Full name</Label>
            <Input
              id="fullName"
              autoComplete="name"
              placeholder="Your name"
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

          <div className="space-y-2">
            <Label htmlFor="organization">Organization</Label>
            <Input
              id="organization"
              placeholder="Company or institution"
              value={form.organizationName}
              onChange={(event) =>
                setForm((current) => ({
                  ...current,
                  organizationName: event.target.value,
                }))
              }
            />
          </div>

          <div className="space-y-2">
            <Label>Interest</Label>
            <Select value={interest} onValueChange={setInterest}>
              <SelectTrigger>
                <SelectValue placeholder="Select interest" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="hosted">Hosted workflows</SelectItem>
                <SelectItem value="api">API integration</SelectItem>
                <SelectItem value="enterprise">Enterprise deployment</SelectItem>
                <SelectItem value="government">Government use case</SelectItem>
                <SelectItem value="security">Security review</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2 sm:col-span-2">
            <Label htmlFor="message">Message</Label>
            <Textarea
              id="message"
              placeholder="Tell us what you want to build with IdentityCore."
              value={form.message}
              onChange={(event) =>
                setForm((current) => ({
                  ...current,
                  message: event.target.value,
                }))
              }
              required
            />
          </div>

          <div className="sm:col-span-2">
            <Button
              type="submit"
              size="lg"
              className="w-full rounded-xl"
              disabled={submitting}
            >
              {submitting ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <ArrowRight className="h-4 w-4" />
              )}
              Send message
            </Button>
          </div>
        </form>

        <p className="mt-6 text-center text-sm text-muted-foreground">
          Want to start immediately?{" "}
          <Link href="/register" className="font-medium text-blue-600">
            Create workspace
          </Link>
        </p>
      </CardContent>
    </Card>
  );
}
