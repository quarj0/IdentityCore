import Link from "next/link";
import {
  ArrowRight,
  Building2,
  Mail,
  MessageSquare,
  ShieldCheck,
} from "lucide-react";
import {
  Badge,
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
} from "@identitycore/ui";
import { MarketingHeader } from "@/components/marketing/marketing-header";
import { MarketingFooter } from "@/components/marketing/marketing-footer";

export default function ContactPage() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <MarketingHeader activePath="/contact" />

      <main id="main-content">
        <section className="relative overflow-hidden">
          <div className="absolute inset-x-0 top-0 -z-10 h-[640px] bg-[radial-gradient(circle_at_top_left,rgba(37,99,235,0.16),transparent_34%),linear-gradient(180deg,#ffffff_0%,#f8fafc_100%)]" />

          <div className="mx-auto grid max-w-7xl gap-16 px-6 py-24 lg:grid-cols-[0.9fr_1.1fr] lg:items-start lg:py-32">
            <div>
              <Badge variant="secondary" className="rounded-full px-3 py-1">
                Contact
              </Badge>

              <h1 className="mt-6 max-w-5xl text-5xl font-semibold tracking-tight sm:text-6xl lg:text-7xl lg:leading-[0.98]">
                Talk to us about identity infrastructure.
              </h1>

              <p className="mt-7 max-w-2xl text-lg leading-8 text-muted-foreground">
                Whether you are exploring hosted workflows, provider
                orchestration, enterprise governance, or future dedicated
                deployment options, we can help you plan the right path.
              </p>

              <div className="mt-10 grid gap-4">
                {[
                  [
                    "Sales and partnerships",
                    "Discuss pricing, use cases, and pilots.",
                    Building2,
                  ],
                  [
                    "Security and compliance",
                    "Ask about privacy, governance, and deployment controls.",
                    ShieldCheck,
                  ],
                  [
                    "Technical questions",
                    "Understand APIs, workflows, providers, and integration paths.",
                    MessageSquare,
                  ],
                ].map(([title, description, Icon]) => {
                  const LucideIcon = Icon as typeof Building2;

                  return (
                    <div
                      key={title as string}
                      className="flex gap-3 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm"
                    >
                      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-blue-50 text-blue-700">
                        <LucideIcon className="h-5 w-5" />
                      </div>
                      <div>
                        <p className="text-sm font-semibold">
                          {title as string}
                        </p>
                        <p className="mt-1 text-sm leading-6 text-muted-foreground">
                          {description as string}
                        </p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            <Card className="rounded-[2rem] border-slate-200/80 bg-white/90 shadow-[0_24px_80px_rgba(15,23,42,0.12)] backdrop-blur">
              <CardHeader>
                <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-blue-50 text-blue-700 ring-1 ring-blue-100">
                  <Mail className="h-5 w-5" />
                </div>
                <CardTitle>Send a message</CardTitle>
                <CardDescription>
                  This is a UI-only form for now. We will connect it later.
                </CardDescription>
              </CardHeader>

              <CardContent>
                <form className="grid gap-5 sm:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="fullName">Full name</Label>
                    <Input
                      id="fullName"
                      autoComplete="name"
                      placeholder="Your name"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="email">Business email</Label>
                    <Input
                      id="email"
                      type="email"
                      autoComplete="email"
                      placeholder="you@company.com"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="organization">Organization</Label>
                    <Input
                      id="organization"
                      placeholder="Company or institution"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label>Interest</Label>
                    <Select>
                      <SelectTrigger>
                        <SelectValue placeholder="Select interest" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="hosted">Hosted workflows</SelectItem>
                        <SelectItem value="api">API integration</SelectItem>
                        <SelectItem value="enterprise">
                          Enterprise deployment
                        </SelectItem>
                        <SelectItem value="government">
                          Government use case
                        </SelectItem>
                        <SelectItem value="security">
                          Security review
                        </SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2 sm:col-span-2">
                    <Label htmlFor="message">Message</Label>
                    <Textarea
                      id="message"
                      placeholder="Tell us what you want to build with IdentityCore."
                    />
                  </div>

                  <div className="sm:col-span-2">
                    <Button
                      type="button"
                      size="lg"
                      className="w-full rounded-xl"
                    >
                      Send message
                      <ArrowRight className="h-4 w-4" />
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
          </div>
        </section>
      </main>

      <MarketingFooter />
    </div>
  );
}
