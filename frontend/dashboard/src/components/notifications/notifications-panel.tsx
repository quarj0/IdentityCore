import { Bell } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@identitycore/ui";

const notifications = [
  "Complete organization profile",
  "Verify administrator identity",
  "Create your first workflow",
];

export function NotificationsPanel() {
  return (
    <Card className="rounded-3xl border-slate-200 bg-white shadow-sm">
      <CardHeader>
        <CardTitle>Notifications</CardTitle>
      </CardHeader>

      <CardContent className="space-y-3">
        {notifications.map((item) => (
          <div
            key={item}
            className="flex gap-3 rounded-2xl border border-slate-200 bg-slate-50 p-4"
          >
            <Bell className="mt-0.5 h-4 w-4 text-blue-600" />
            <p className="text-sm font-medium">{item}</p>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
