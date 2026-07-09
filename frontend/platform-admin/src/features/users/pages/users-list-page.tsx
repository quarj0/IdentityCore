"use client";

import { useMemo, useState } from "react";
import { Search, SlidersHorizontal } from "lucide-react";
import { Button, Input } from "@identitycore/ui";
import { EmptyState } from "@/components/feedback/empty-state";
import { PageHeader } from "@/components/shared/page-header";
import { InviteAdminDialog } from "@/features/users/components/invite-admin-dialog";
import { adminUsers } from "@/features/users/mock-data";
import { UsersTable } from "@/features/users/tables/users-table";

export function UsersListPage() {
  const [query, setQuery] = useState("");

  const filteredUsers = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();

    if (!normalizedQuery) {
      return adminUsers;
    }

    return adminUsers.filter((user) =>
      [
        user.name,
        user.email,
        user.role,
        user.status,
        user.department,
        user.location,
        user.riskLevel,
      ]
        .join(" ")
        .toLowerCase()
        .includes(normalizedQuery),
    );
  }, [query]);

  return (
    <div className="space-y-6 bg-white text-slate-950">
      <PageHeader
        eyebrow="Platform access"
        title="Platform admins"
        description="Manage IdentityCore employee access, roles, permissions, invitations, sessions, MFA status and account security."
        actions={
          <>
            <Button variant="outline">Export</Button>
            <InviteAdminDialog />
          </>
        }
      />

      <section className="rounded-3xl border border-slate-200 bg-white p-4 shadow-sm">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <div className="relative w-full lg:max-w-md">
            <Search
              className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-400"
              aria-hidden="true"
            />

            <Input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search admins..."
              className="pl-10"
              aria-label="Search platform admins"
            />
          </div>

          <div className="flex flex-wrap gap-2">
            <Button variant="outline">Role</Button>
            <Button variant="outline">Status</Button>
            <Button variant="outline">Security</Button>
            <Button variant="outline">
              <SlidersHorizontal className="mr-2 size-4" aria-hidden="true" />
              More filters
            </Button>
          </div>
        </div>
      </section>

      {filteredUsers.length > 0 ? (
        <UsersTable users={filteredUsers} />
      ) : (
        <EmptyState
          title="No platform admins found"
          description="No admin matches the current search or filters. Clear your search and try again."
        />
      )}
    </div>
  );
}
