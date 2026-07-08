import { NotificationsPanel } from "@/components/notifications/notifications-panel";
import { PageHeading } from "@/components/shared/page-heading";

export default function NotificationsPage() {
  return (
    <div className="space-y-8">
      <PageHeading
        title="Notifications"
        description="Review workspace alerts, onboarding reminders, and system updates."
      />

      <NotificationsPanel />
    </div>
  );
}
