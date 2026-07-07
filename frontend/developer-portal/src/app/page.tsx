"use client";

import { useState } from "react";
import Link from "next/link";
import {
  BookOpen,
  Check,
  ChevronRight,
  Code2,
  Copy,
  Fingerprint,
  KeyRound,
  PlayCircle,
  ShieldCheck,
  Webhook,
} from "lucide-react";
import {
  Badge,
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@identitycore/ui";

const codeSnippets = {
  curl: `curl -X POST https://api.identitycore.com/v1/verifications \\
  -H "Authorization: Bearer ic_live_sk_..." \\
  -H "Content-Type: application/json" \\
  -d '{
    "policy_id": "pol-standard-kyc",
    "email": "user@example.com",
    "subject": {
      "first_name": "James",
      "last_name": "Okafor"
    }
  }'`,
  node: `import { IdentityCore } from "@identitycore/sdk";

const client = new IdentityCore({
  apiKey: process.env.IDENTITYCORE_SECRET_KEY!,
});

const session = await client.verifications.create({
  policyId: "pol-standard-kyc",
  email: "user@example.com",
  subject: {
    firstName: "James",
    lastName: "Okafor",
  },
});

console.log(session.url);`,
  python: `from identitycore import Client

client = Client(api_key="ic_live_sk_...")

session = client.verifications.create(
    policy_id="pol-standard-kyc",
    email="user@example.com",
    subject={
        "first_name": "James",
        "last_name": "Okafor",
    },
)

print(session.url)`,
};

const quickstartSteps = [
  {
    title: "Create a secret key",
    description:
      "Generate a server-side key from the dashboard and store it in your backend environment.",
    icon: KeyRound,
  },
  {
    title: "Create a verification session",
    description:
      "Call the API with a policy id, subject payload, and your own internal metadata.",
    icon: PlayCircle,
  },
  {
    title: "Handle the result lifecycle",
    description:
      "Listen to webhooks, pull the final decision object, and route reviewers when needed.",
    icon: Webhook,
  },
];

const navGroups = [
  {
    title: "Getting started",
    items: ["Quickstart", "Authentication", "Error handling"],
  },
  {
    title: "Core API",
    items: ["Create verification", "Retrieve verification", "Policies"],
  },
  {
    title: "Platform",
    items: ["Webhooks", "Review queues", "Audit exports"],
  },
];

export default function DeveloperPortalPage() {
  const [lang, setLang] = useState<keyof typeof codeSnippets>("curl");
  const [copied, setCopied] = useState(false);

  async function copyCode() {
    await navigator.clipboard.writeText(codeSnippets[lang]);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1500);
  }

  return (
    <div className="min-h-screen">
      <div className="mx-auto grid min-h-screen max-w-[1600px] lg:grid-cols-[280px_minmax(0,1fr)_520px]">
        <aside className="border-r border-border/70 bg-background/72 px-5 py-6 backdrop-blur-xl">
          <div className="sticky top-6 space-y-8">
            <Link href="/" className="flex items-center gap-3">
              <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-primary text-primary-foreground">
                <Fingerprint className="h-5 w-5" />
              </div>
              <div>
                <div className="text-sm font-semibold tracking-[0.18em]">IDENTITYCORE</div>
                <div className="text-xs text-muted-foreground">Developer portal</div>
              </div>
            </Link>

            <div className="rounded-2xl border border-border/70 bg-card/70 p-4">
              <div className="flex items-center gap-2 text-sm font-semibold text-foreground">
                <ShieldCheck className="h-4 w-4 text-primary" />
                Production checklist
              </div>
              <p className="mt-2 text-sm leading-6 text-muted-foreground">
                Use secret keys on the server, keep policies versioned, and subscribe to verification status webhooks before launch.
              </p>
            </div>

            <nav className="space-y-6">
              {navGroups.map((group) => (
                <div key={group.title}>
                  <div className="mb-2 text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                    {group.title}
                  </div>
                  <div className="space-y-1">
                    {group.items.map((item, index) => (
                      <button
                        key={item}
                        className={`flex w-full items-center justify-between rounded-xl px-3 py-2 text-left text-sm transition-colors ${
                          index === 0 && group.title === "Getting started"
                            ? "bg-primary text-primary-foreground"
                            : "text-muted-foreground hover:bg-secondary/70 hover:text-foreground"
                        }`}
                      >
                        <span>{item}</span>
                        <ChevronRight className="h-3.5 w-3.5" />
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </nav>
          </div>
        </aside>

        <main className="px-6 py-8 lg:px-10 xl:px-14">
          <div className="mx-auto max-w-4xl space-y-10">
            <section className="space-y-5">
              <Badge variant="info" className="px-4 py-1.5">
                <Code2 className="h-3.5 w-3.5" />
                API quickstart
              </Badge>
              <h1 className="text-4xl font-semibold tracking-tight text-foreground sm:text-5xl">
                Launch a verification flow with clean server-side primitives.
              </h1>
              <p className="max-w-3xl text-lg leading-8 text-muted-foreground">
                IdentityCore is built so your integration reads clearly: create a session, send the user to the hosted flow, listen for updates, and escalate to reviewers only when the policy says so.
              </p>
              <div className="flex flex-wrap gap-3">
                <Button asChild>
                  <a href="http://localhost:3000">Open dashboard</a>
                </Button>
                <Button asChild variant="outline">
                  <Link href="/">Back to product site</Link>
                </Button>
              </div>
            </section>

            <section className="grid gap-5 md:grid-cols-3">
              {quickstartSteps.map((step) => {
                const Icon = step.icon;
                return (
                  <Card key={step.title}>
                    <CardHeader className="space-y-4">
                      <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-primary/10 text-primary">
                        <Icon className="h-5 w-5" />
                      </div>
                      <div className="space-y-2">
                        <CardTitle className="text-lg">{step.title}</CardTitle>
                        <CardDescription>{step.description}</CardDescription>
                      </div>
                    </CardHeader>
                  </Card>
                );
              })}
            </section>

            <section className="space-y-5">
              <div className="space-y-2">
                <h2 className="text-2xl font-semibold tracking-tight text-foreground">
                  Integration flow
                </h2>
                <p className="text-base leading-7 text-muted-foreground">
                  Start with one route on your backend and one redirect in your frontend.
                </p>
              </div>

              <Tabs defaultValue="session" className="space-y-4">
                <TabsList>
                  <TabsTrigger value="session">Create session</TabsTrigger>
                  <TabsTrigger value="redirect">Redirect user</TabsTrigger>
                  <TabsTrigger value="webhooks">Process webhooks</TabsTrigger>
                </TabsList>
                <TabsContent value="session">
                  <Card>
                    <CardContent className="space-y-3 p-6">
                      <div className="flex gap-3 text-sm text-muted-foreground">
                        <BookOpen className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
                        Build the session server-side so your policy IDs, audit metadata, and internal identifiers stay under your control.
                      </div>
                    </CardContent>
                  </Card>
                </TabsContent>
                <TabsContent value="redirect">
                  <Card>
                    <CardContent className="space-y-3 p-6">
                      <div className="flex gap-3 text-sm text-muted-foreground">
                        <PlayCircle className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
                        Present the hosted verification URL and let the user complete capture in a branded, guided flow.
                      </div>
                    </CardContent>
                  </Card>
                </TabsContent>
                <TabsContent value="webhooks">
                  <Card>
                    <CardContent className="space-y-3 p-6">
                      <div className="flex gap-3 text-sm text-muted-foreground">
                        <Webhook className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
                        Subscribe to lifecycle updates so your product reacts to approval, manual review, and expiration events in near real time.
                      </div>
                    </CardContent>
                  </Card>
                </TabsContent>
              </Tabs>
            </section>
          </div>
        </main>

        <section className="hidden border-l border-border/70 bg-slate-950 text-slate-100 lg:flex">
          <div className="sticky top-0 flex h-screen w-full flex-col">
            <div className="flex items-center justify-between border-b border-white/8 px-6 py-5">
              <div>
                <div className="text-sm font-semibold">Request example</div>
                <div className="text-xs text-slate-400">
                  Copy a starter snippet and wire it into your backend route.
                </div>
              </div>
              <Button
                variant="ghost"
                size="icon"
                className="text-slate-300 hover:bg-white/10 hover:text-white"
                onClick={copyCode}
              >
                {copied ? <Check className="h-4 w-4 text-emerald-400" /> : <Copy className="h-4 w-4" />}
              </Button>
            </div>

            <div className="flex gap-2 px-6 py-4">
              {(["curl", "node", "python"] as const).map((entry) => (
                <button
                  key={entry}
                  onClick={() => setLang(entry)}
                  className={`rounded-full px-3 py-1.5 text-xs font-medium transition-colors ${
                    lang === entry
                      ? "bg-cyan-400/20 text-cyan-200"
                      : "bg-white/5 text-slate-400 hover:bg-white/10 hover:text-slate-100"
                  }`}
                >
                  {entry === "node" ? "Node.js" : entry === "python" ? "Python" : "cURL"}
                </button>
              ))}
            </div>

            <div className="flex-1 overflow-auto px-6 pb-6">
              <pre className="rounded-3xl border border-white/8 bg-black/30 p-6 font-mono text-[13px] leading-6 text-slate-300">
                <code>{codeSnippets[lang]}</code>
              </pre>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
