import Link from "next/link";
import { ChevronRight } from "lucide-react";
import { EmptyState } from "@/components/feedback/empty-state";
import { AdminActivityCard } from "@/features/users/components/admin-activity-card";
import { AdminHeader } from "@/features/users/components/admin-header";
import { AdminPermissionsCard } from "@/features/users/components/admin-permissions-card";
import { AdminRolesCard } from "@/features/users/components/admin-roles-card";
import { AdminSecurityCard } from "@/features/users/components/admin-security-card";
import { AdminSessionsCard } from "@/features/users/components/admin-sessions-card";
import { AdminSummaryCards } from "../components/admin-summary-cards"; 
import { getAdminUserById } from "@/features/users/mock-data";

type AdminDetailPageProps = {
  userId: string;
};

export function AdminDetailPage({ userId }: AdminDetailPageProps) {
  const user = getAdminUserById(userId);

  if (!user) {
    return (
      <EmptyState
        title="Admin user not found"
        description="This admin may have been removed, disabled or moved to another environment."
      />
    );
  }

  return (
    <div className="space-y-6 bg-white text-slate-950">
      <nav
        aria-label="Breadcrumb"
        className="flex items-center gap-2 text-sm text-slate-500"
      >
        <Link
          href="/users"
          className="outline-none hover:text-blue-700 focus-visible:ring-2 focus-visible:ring-blue-500"
        >
          Platform admins
        </Link>
        <ChevronRight className="size-4" aria-hidden="true" />
        <span className="text-slate-700">{user.name}</span>
      </nav>

      <AdminHeader user={user} />

      <AdminSummaryCards user={user} />

      <div className="grid gap-4 xl:grid-cols-3">
        <div className="space-y-4 xl:col-span-2">
          <AdminPermissionsCard />
          <AdminSessionsCard />
          <AdminActivityCard />
        </div>

        <div className="space-y-4">
          <AdminRolesCard user={user} />
          <AdminSecurityCard user={user} />
        </div>
      </div>
    </div>
  );
}
