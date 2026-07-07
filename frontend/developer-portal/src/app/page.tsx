"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Book, Code, Key, Webhook, Play, Terminal, Fingerprint, ChevronRight, Copy, Check } from "lucide-react";
import { Button, Card, CardContent, CardDescription, CardHeader, CardTitle, Tabs, TabsList, TabsTrigger, TabsContent } from "@identitycore/ui";

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
  node: `const { IdentityCore } = require('@identitycore/sdk');
const client = new IdentityCore({ apiKey: 'ic_live_sk_...' });

const session = await client.verifications.create({
  policyId: 'pol-standard-kyc',
  email: 'user@example.com',
  subject: {
    firstName: 'James',
    lastName: 'Okafor'
  }
});

console.log(\`Verification URL: \${session.url}\`);`,
  python: `from identitycore import Client

client = Client(api_key="ic_live_sk_...")

session = client.verifications.create(
    policy_id="pol-standard-kyc",
    email="user@example.com",
    subject={
        "first_name": "James",
        "last_name": "Okafor"
    }
)

print(f"Verification URL: {session.url}")`,
};

export default function DevPortalPage() {
  const [lang, setLang] = useState<keyof typeof codeSnippets>("curl");
  const [copied, setCopied] = useState(false);

  const copyCode = () => {
    navigator.clipboard.writeText(codeSnippets[lang]);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      {/* Sidebar */}
      <aside className="w-64 border-r border-border bg-muted/20 flex flex-col shrink-0">
        <div className="h-16 px-6 border-b border-border flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-primary text-primary-foreground">
            <Fingerprint className="h-4.5 w-4.5" />
          </div>
          <span className="font-semibold text-sm tracking-tight">IdentityCore Docs</span>
        </div>
        <nav className="flex-1 p-4 space-y-6 overflow-y-auto">
          <div>
            <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wider px-3 mb-2">Getting Started</div>
            <div className="space-y-1">
              <Link href="#" className="flex items-center gap-2 px-3 py-1.5 text-sm rounded-md bg-secondary text-secondary-foreground font-medium">
                <Book className="h-4 w-4" />
                Quickstart
              </Link>
              <Link href="#" className="flex items-center gap-2 px-3 py-1.5 text-sm rounded-md text-muted-foreground hover:bg-muted/50 hover:text-foreground transition-colors">
                <Key className="h-4 w-4" />
                Authentication
              </Link>
              <Link href="#" className="flex items-center gap-2 px-3 py-1.5 text-sm rounded-md text-muted-foreground hover:bg-muted/50 hover:text-foreground transition-colors">
                <Webhook className="h-4 w-4" />
                Webhooks
              </Link>
            </div>
          </div>

          <div>
            <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wider px-3 mb-2">API Reference</div>
            <div className="space-y-1">
              <Link href="#" className="flex items-center gap-2 px-3 py-1.5 text-sm rounded-md text-muted-foreground hover:bg-muted/50 hover:text-foreground transition-colors">
                <Play className="h-4 w-4" />
                Create Verification
              </Link>
              <Link href="#" className="flex items-center gap-2 px-3 py-1.5 text-sm rounded-md text-muted-foreground hover:bg-muted/50 hover:text-foreground transition-colors">
                <Code className="h-4 w-4" />
                Retrieve Verification
              </Link>
            </div>
          </div>
        </nav>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Side: Documentation */}
        <main className="flex-1 overflow-y-auto p-8 lg:p-12 space-y-6 max-w-3xl">
          <div className="space-y-2">
            <h1 className="text-3xl font-extrabold tracking-tight">API Quickstart</h1>
            <p className="text-sm text-muted-foreground leading-relaxed">
              Learn how to quickly initialize verification sessions using the IdentityCore API. Get started with our SDKs or raw curl requests.
            </p>
          </div>

          <div className="space-y-4">
            <h2 className="text-xl font-bold tracking-tight">1. Authenticate your requests</h2>
            <p className="text-sm text-muted-foreground leading-relaxed">
              Include your secret key in the authorization header of your HTTP request. You can create and manage keys inside the Developer section of your <a href="http://localhost:3000" className="text-primary hover:underline font-medium">Dashboard</a>.
            </p>
          </div>

          <div className="space-y-4">
            <h2 className="text-xl font-bold tracking-tight">2. Create a Verification Session</h2>
            <p className="text-sm text-muted-foreground leading-relaxed">
              Post to `/v1/verifications` specifying the verification policy ID (e.g., standard KYC) and email address of the subject.
            </p>
            <p className="text-sm text-muted-foreground leading-relaxed">
              The API will return a unique `verification_url` which you should present to the subject to capture consent, document upload, and selfie.
            </p>
          </div>
        </main>

        {/* Right Side: Code Block Preview (Stripe/Supabase style) */}
        <section className="w-[450px] border-l border-border bg-slate-950 text-slate-200 hidden xl:flex flex-col shrink-0">
          <div className="h-16 px-6 border-b border-slate-900 flex items-center justify-between">
            <div className="flex gap-2">
              {(["curl", "node", "python"] as const).map((l) => (
                <button
                  key={l}
                  onClick={() => setLang(l)}
                  className={`text-xs font-mono px-2.5 py-1 rounded transition-colors ${
                    lang === l ? "bg-slate-800 text-white font-semibold" : "text-slate-400 hover:text-white"
                  }`}
                >
                  {l === "node" ? "Node.js" : l === "python" ? "Python" : "cURL"}
                </button>
              ))}
            </div>
            <Button variant="ghost" size="icon" className="h-8 w-8 text-slate-400 hover:text-white hover:bg-slate-800" onClick={copyCode}>
              {copied ? <Check className="h-4 w-4 text-emerald-400" /> : <Copy className="h-4 w-4" />}
            </Button>
          </div>
          <div className="flex-1 p-6 font-mono text-xs overflow-auto leading-relaxed bg-slate-950 text-slate-300">
            <pre className="whitespace-pre">{codeSnippets[lang]}</pre>
          </div>
        </section>
      </div>
    </div>
  );
}
