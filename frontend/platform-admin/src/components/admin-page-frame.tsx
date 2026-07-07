import { PageHeader } from "@identitycore/ui";
import { AdminShell } from "@/components/admin-shell";

export function AdminPageFrame({
  title,
  description,
  actions,
  children,
}: {
  title: string;
  description: string;
  actions?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <AdminShell>
      <div className="space-y-6">
        <PageHeader title={title} description={description} actions={actions} />
        {children}
      </div>
    </AdminShell>
  );
}
