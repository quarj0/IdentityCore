import type { Metadata } from "next";
import { Plus, Copy, Trash2, Key } from "lucide-react";
import {
  Card,
  CardContent,
  Badge,
  Button,
  Callout,
  PageHeader,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@identitycore/ui";

export const metadata: Metadata = { title: "API Keys" };

const apiKeys = [
  { id: "key-001", name: "Production Key", prefix: "ic_live_sk_", suffix: "...9xKq", created: "May 1, 2026", lastUsed: "Jul 6, 2026", status: "active" },
  { id: "key-002", name: "Staging Key", prefix: "ic_test_sk_", suffix: "...4mPw", created: "Apr 14, 2026", lastUsed: "Jul 5, 2026", status: "active" },
  { id: "key-003", name: "CI/CD Key", prefix: "ic_test_sk_", suffix: "...7rNv", created: "Mar 20, 2026", lastUsed: "Jun 28, 2026", status: "active" },
  { id: "key-004", name: "Old Dev Key", prefix: "ic_test_sk_", suffix: "...2bHs", created: "Jan 10, 2026", lastUsed: "Feb 15, 2026", status: "revoked" },
];

export default function ApiKeysPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="API keys"
        description="Manage secret keys for server-side API authentication."
        actions={
          <Button id="create-api-key">
            <Plus className="h-4 w-4" />
            Create key
          </Button>
        }
      />

      <Callout variant="warning" icon={<Key className="h-4 w-4" />}>
        Secret keys grant full access to your organization. Store them securely and never expose them in client-side code or version control.
      </Callout>

      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow className="hover:bg-transparent">
                <TableHead>Name</TableHead>
                <TableHead>Key</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="hidden lg:table-cell">Created</TableHead>
                <TableHead className="hidden lg:table-cell">Last used</TableHead>
                <TableHead className="w-20" />
              </TableRow>
            </TableHeader>
            <TableBody>
              {apiKeys.map((k) => (
                <TableRow key={k.id} id={`key-row-${k.id}`}>
                  <TableCell className="font-medium">{k.name}</TableCell>
                  <TableCell>
                    <code className="rounded bg-muted px-2 py-1 font-mono text-xs">
                      {k.prefix}••••••••{k.suffix}
                    </code>
                  </TableCell>
                  <TableCell>
                    <Badge variant={k.status === "active" ? "success" : "secondary"}>
                      {k.status === "active" ? "Active" : "Revoked"}
                    </Badge>
                  </TableCell>
                  <TableCell className="hidden text-muted-foreground lg:table-cell">{k.created}</TableCell>
                  <TableCell className="hidden text-muted-foreground lg:table-cell">{k.lastUsed}</TableCell>
                  <TableCell>
                    <div className="flex items-center justify-end gap-1">
                      <Button variant="ghost" size="icon" className="h-8 w-8" id={`copy-key-${k.id}`} title="Copy key">
                        <Copy className="h-3.5 w-3.5" />
                      </Button>
                      {k.status === "active" ? (
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8 text-destructive hover:text-destructive"
                          id={`revoke-key-${k.id}`}
                          title="Revoke key"
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </Button>
                      ) : null}
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
