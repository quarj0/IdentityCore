import { Button } from "@identitycore/ui";
import type { AdminUser } from "@/features/users/mock-data";
import { AdminStatusPill } from "@/features/users/components/admin-status-pill";
import { DisableAdminDialog } from "@/features/users/components/disable-admin-dialog";

type AdminHeaderProps = {
  user: AdminUser;
};

export function AdminHeader({ user }: AdminHeaderProps) {
  return (
    <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
        <div className="flex gap-4">
          <div className="flex size-14 shrink-0 items-center justify-center rounded-3xl bg-blue-50 text-lg font-semibold text-blue-700 ring-1 ring-blue-100">
            {user.initials}
          </div>

          <div>
            <div className="flex flex-wrap items-center gap-3">
              <h1 className="text-2xl font-semibold tracking-tight text-slate-950">
                {user.name}
              </h1>
              <AdminStatusPill status={user.status} />
            </div>

            <p className="mt-2 text-sm text-slate-600">
              {user.email} · {user.department} · {user.location}
            </p>

            <dl className="mt-5 grid gap-3 sm:grid-cols-3">
              <div>
                <dt className="text-xs uppercase tracking-wide text-slate-500">
                  Role
                </dt>
                <dd className="mt-1 text-sm font-medium text-slate-950">
                  {user.role}
                </dd>
              </div>

              <div>
                <dt className="text-xs uppercase tracking-wide text-slate-500">
                  Joined
                </dt>
                <dd className="mt-1 text-sm font-medium text-slate-950">
                  {user.joinedAt}
                </dd>
              </div>

              <div>
                <dt className="text-xs uppercase tracking-wide text-slate-500">
                  Last active
                </dt>
                <dd className="mt-1 text-sm font-medium text-slate-950">
                  {user.lastActiveAt}
                </dd>
              </div>
            </dl>
          </div>
        </div>

        <div className="flex flex-wrap gap-2">
          <Button variant="outline">Reset MFA</Button>
          <Button variant="outline">Revoke sessions</Button>
          {user.status !== "disabled" ? (
            <DisableAdminDialog adminName={user.name} />
          ) : null}
        </div>
      </div>
    </section>
  );
}
