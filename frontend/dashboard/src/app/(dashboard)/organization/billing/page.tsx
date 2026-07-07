import type { Metadata } from "next";
import { Badge, Button, Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle, Progress } from "@identitycore/ui";
import { CreditCard, Check, ArrowUpRight } from "lucide-react";

export const metadata: Metadata = { title: "Billing & Plans" };

const invoices = [
  { id: "inv-3", amount: "$149.00", status: "Paid", date: "2026-07-01" },
  { id: "inv-2", amount: "$149.00", status: "Paid", date: "2026-06-01" },
  { id: "inv-1", amount: "$149.00", status: "Paid", date: "2026-05-01" },
];

export default function BillingPage() {
  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-xl font-semibold tracking-tight">Billing & Subscription</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Manage your organization's subscription plan, usage, and invoices.
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {/* Active plan card */}
        <Card>
          <CardHeader>
            <div className="flex justify-between items-start">
              <div>
                <CardTitle className="text-lg">Active Plan</CardTitle>
                <CardDescription>You are currently on the Growth tier.</CardDescription>
              </div>
              <Badge variant="success">Active</Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="text-3xl font-bold">$149<span className="text-sm font-normal text-muted-foreground"> / month</span></div>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Verification credits used</span>
                <span className="font-medium">1,420 / 5,000</span>
              </div>
              <Progress value={28.4} />
            </div>
          </CardContent>
          <CardFooter className="border-t border-border pt-4 flex gap-2 justify-end">
            <Button variant="outline" size="sm" id="upgrade-plan">Upgrade Plan</Button>
          </CardFooter>
        </Card>

        {/* Payment method card */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Payment Method</CardTitle>
            <CardDescription>Your monthly invoice is charged to this card.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center gap-3 rounded-lg border border-border p-4 bg-muted/20">
              <div className="flex h-10 w-10 items-center justify-center rounded-md border border-border bg-background">
                <CreditCard className="h-5 w-5 text-muted-foreground" />
              </div>
              <div>
                <div className="font-medium text-sm text-foreground">Visa ending in 4242</div>
                <div className="text-xs text-muted-foreground">Expires 12/28</div>
              </div>
            </div>
          </CardContent>
          <CardFooter className="border-t border-border pt-4 flex gap-2 justify-end">
            <Button variant="outline" size="sm" id="update-payment">Update Card</Button>
          </CardFooter>
        </Card>
      </div>

      {/* Invoice history */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Billing History</CardTitle>
          <CardDescription>View and download past invoices.</CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border bg-muted/40">
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground">Invoice ID</th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground">Amount</th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground">Date</th>
                <th className="px-6 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {invoices.map((inv) => (
                <tr key={inv.id} className="transition-colors hover:bg-muted/30">
                  <td className="px-6 py-3.5 font-mono text-xs text-muted-foreground">{inv.id}</td>
                  <td className="px-6 py-3.5 font-medium text-foreground">{inv.amount}</td>
                  <td className="px-6 py-3.5">
                    <Badge variant="success">{inv.status}</Badge>
                  </td>
                  <td className="px-6 py-3.5 text-muted-foreground">{inv.date}</td>
                  <td className="px-6 py-3.5 text-right">
                    <Button variant="ghost" size="sm" className="gap-1 text-xs" id={`download-${inv.id}`}>
                      Download
                      <ArrowUpRight className="h-3 w-3" />
                    </Button>
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
