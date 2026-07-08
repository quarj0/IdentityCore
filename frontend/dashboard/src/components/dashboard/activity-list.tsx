import { Activity } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@identitycore/ui";
import { recentActivity } from "@/data/mock-dashboard";

export function ActivityList() {
  return (
    <Card className="rounded-3xl border-slate-200 bg-white shadow-sm">
      <CardHeader>
        <CardTitle>Recent activity</CardTitle>
      </CardHeader>

      <CardContent className="space-y-4">
        {recentActivity.map((activity) => (
          <div key={activity.title} className="flex gap-3">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-slate-100 text-slate-600">
              <Activity className="h-4 w-4" />
            </div>

            <div>
              <p className="text-sm font-medium">{activity.title}</p>
              <p className="text-sm leading-6 text-slate-600">
                {activity.description}
              </p>
              <p className="mt-1 text-xs text-slate-400">{activity.time}</p>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
