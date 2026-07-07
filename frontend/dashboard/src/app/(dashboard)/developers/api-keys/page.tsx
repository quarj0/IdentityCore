import type { Metadata } from "next";
import { Plus, Eye, EyeOff, Copy, Trash2, Key } from "lucide-react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
  Badge,
  Button,
} from "@identitycore/ui";

export const metadata: Metadata = { title: "API Keys" };

const apiKeys = [
  { id: "key-001", name: "Production Key", prefix: "ic_live_sk_", suffix: "...9xKq", created: "2026-05-01", lastUsed: "2026-07-06", status: "active" },
  { id: "key-002", name: "Staging Key", prefix: "ic_test_sk_", suffix: "...4mPw", created: "2026-04-14", lastUsed: "2026-07-05", status: "active" },
  { id: "key-003", name: "CI/CD Key", prefix: "ic_test_sk_", suffix: "...7rNv", created: "2026-03-20", lastUsed: "2026-06-28", status: "active" },
  { id: "key-004", name: "Old Dev Key", prefix: "ic_test_sk_", suffix: "...2bHs", created: "2026-01-10", lastUsed: "2026-02-15", status: "revoked" },
];

export default function ApiKeysPage() {
  return (
    <div className="p-6 space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-xl font-semibold tracking-tight">API Keys</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Manage API keys for authenticating your application with IdentityCore.
          </p>
        </div>
        <Button id="create-api-key" className="gap-2 self-start sm:self-auto">
          <Plus className="h-4 w-4" />
          Create Key
        </Button>
      </div>

      {/* Security notice */}
      <div className="flex items-start gap-3 rounded-lg border border-amber-200 bg-amber-50 p-4 dark:border-amber-800/40 dark:bg-amber-900/10">
        <Key className="mt-0.5 h-4 w-4 shrink-0 text-amber-600 dark:text-amber-400" />
        <p className="text-sm text-amber-800 dark:text-amber-300">
          API keys grant full access to your organization. Never expose secret keys in client-side code, version control, or public channels.
        </p>
      </div>

      <Card>
        <CardContent className="p-0">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border bg-muted/40">
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground">Name</th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground">Key</th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground">Status</th>
                <th className="hidden px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground lg:table-cell">Created</th>
                <th className="hidden px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground lg:table-cell">Last Used</th>
                <th className="px-6 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {apiKeys.map((k) => (
                <tr key={k.id} id={`key-row-${k.id}`} className="transition-colors hover:bg-muted/30">
                  <td className="px-6 py-3.5 font-medium">{k.name}</td>
                  <td className="px-6 py-3.5">
                    <code className="rounded bg-muted px-2 py-0.5 text-xs font-mono">
                      {k.prefix}••••••••{k.suffix}
                    </code>
                  </td>
                  <td className="px-6 py-3.5">
                    <Badge variant={k.status === "active" ? "success" : "secondary"}>
                      {k.status === "active" ? "Active" : "Revoked"}
                    </Badge>
                  </td>
                  <td className="hidden px-6 py-3.5 text-muted-foreground lg:table-cell">{k.created}</td>
                  <td className="hidden px-6 py-3.5 text-muted-foreground lg:table-cell">{k.lastUsed}</td>
                  <td className="px-6 py-3.5">
                    <div className="flex items-center justify-end gap-1">
                      <Button variant="ghost" size="icon" className="h-7 w-7" id={`copy-key-${k.id}`} title="Copy key">
                        <Copy className="h-3.5 w-3.5" />
                      </Button>
                      {k.status === "active" && (
                        <Button variant="ghost" size="icon" className="h-7 w-7 text-destructive hover:text-destructive" id={`revoke-key-${k.id}`} title="Revoke key">
                          <Trash2 className="h-3.5 w-3.5" />
                        </Button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  );
}
