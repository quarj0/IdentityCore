import type { Metadata } from "next";
import { Badge, Button, Card, CardContent, Input, Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@identitycore/ui";
import { Search, ArrowUpRight, ArrowDownRight, RefreshCw } from "lucide-react";

export const metadata: Metadata = { title: "API Logs" };

const logs = [
  { id: "log-1", method: "POST", endpoint: "/v1/verifications", status: 201, duration: "184ms", ip: "192.168.1.1", time: "2026-07-06 23:59:12" },
  { id: "log-2", method: "GET", endpoint: "/v1/verifications/req_1091", status: 200, duration: "45ms", ip: "192.168.1.1", time: "2026-07-06 23:58:01" },
  { id: "log-3", method: "POST", endpoint: "/v1/verifications", status: 400, duration: "24ms", ip: "184.22.109.5", time: "2026-07-06 23:45:18" },
  { id: "log-4", method: "POST", endpoint: "/v1/policies", status: 201, duration: "112ms", ip: "192.168.1.1", time: "2026-07-06 23:15:00" },
  { id: "log-5", method: "GET", endpoint: "/v1/policies", status: 200, duration: "32ms", ip: "192.168.1.1", time: "2026-07-06 23:14:50" },
  { id: "log-6", method: "POST", endpoint: "/v1/verifications/req_1090/liveness", status: 200, duration: "340ms", ip: "99.88.77.66", time: "2026-07-06 22:50:11" },
];

export default function LogsPage() {
  return (
    <div className="p-6 space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-xl font-semibold tracking-tight">API Logs</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Monitor API request logs and response codes in real time.
          </p>
        </div>
        <Button variant="outline" className="gap-2 self-start sm:self-auto" id="refresh-logs">
          <RefreshCw className="h-4 w-4" />
          Refresh
        </Button>
      </div>

      <div className="flex flex-wrap gap-3">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
          <Input id="search-logs" placeholder="Search by endpoint..." className="pl-8 h-9" />
        </div>
        <Select>
          <SelectTrigger id="filter-log-status" className="w-36 h-9">
            <SelectValue placeholder="All status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All status</SelectItem>
            <SelectItem value="2xx">2xx Success</SelectItem>
            <SelectItem value="4xx">4xx Client Error</SelectItem>
            <SelectItem value="5xx">5xx Server Error</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <Card>
        <CardContent className="p-0">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border bg-muted/40">
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground">Method</th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground">Endpoint</th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground">Status</th>
                <th className="hidden px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground md:table-cell">Duration</th>
                <th className="hidden px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground lg:table-cell">IP Address</th>
                <th className="px-6 py-3 text-right text-xs font-medium uppercase tracking-wider text-muted-foreground">Time</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {logs.map((log) => {
                const isError = log.status >= 400;
                return (
                  <tr key={log.id} className="transition-colors hover:bg-muted/30">
                    <td className="px-6 py-3.5 font-mono text-xs font-bold">
                      <span className={log.method === "POST" ? "text-blue-600" : "text-emerald-600"}>
                        {log.method}
                      </span>
                    </td>
                    <td className="px-6 py-3.5 font-mono text-xs text-foreground">{log.endpoint}</td>
                    <td className="px-6 py-3.5">
                      <Badge variant={isError ? "destructive" : "success"}>
                        {log.status}
                      </Badge>
                    </td>
                    <td className="hidden px-6 py-3.5 text-muted-foreground md:table-cell">{log.duration}</td>
                    <td className="hidden px-6 py-3.5 text-muted-foreground lg:table-cell">{log.ip}</td>
                    <td className="px-6 py-3.5 text-right text-muted-foreground text-xs">{log.time}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  );
}
