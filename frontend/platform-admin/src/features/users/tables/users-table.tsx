import Link from "next/link";
import { MoreHorizontal } from "lucide-react";
import {
  Button,
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@identitycore/ui";
import type { AdminUser } from "@/features/users/mock-data";
import { AdminStatusPill } from "@/features/users/components/admin-status-pill";

type UsersTableProps = {
  users: AdminUser[];
};

export function UsersTable({ users }: UsersTableProps) {
  return (
    <div className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
      <div className="overflow-x-auto">
        <table className="w-full min-w-262.5 text-left text-sm">
          <thead className="border-b border-slate-200 bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
            <tr>
              <th scope="col" className="px-5 py-4 font-medium">
                Admin
              </th>
              <th scope="col" className="px-5 py-4 font-medium">
                Status
              </th>
              <th scope="col" className="px-5 py-4 font-medium">
                Role
              </th>
              <th scope="col" className="px-5 py-4 font-medium">
                Department
              </th>
              <th scope="col" className="px-5 py-4 font-medium">
                Security
              </th>
              <th scope="col" className="px-5 py-4 font-medium">
                Sessions
              </th>
              <th scope="col" className="px-5 py-4 font-medium">
                Last active
              </th>
              <th scope="col" className="px-5 py-4 text-right font-medium">
                Actions
              </th>
            </tr>
          </thead>

          <tbody className="divide-y divide-slate-200">
            {users.map((user) => (
              <tr key={user.id} className="transition hover:bg-slate-50">
                <td className="px-5 py-4">
                  <div className="flex items-center gap-3">
                    <div className="flex size-10 shrink-0 items-center justify-center rounded-2xl bg-blue-50 text-sm font-semibold text-blue-700 ring-1 ring-blue-100">
                      {user.initials}
                    </div>

                    <div>
                      <Link
                        href={`/users/${user.id}`}
                        className="font-medium text-slate-950 outline-none hover:text-blue-700 focus-visible:ring-2 focus-visible:ring-blue-500"
                      >
                        {user.name}
                      </Link>
                      <p className="mt-1 text-xs text-slate-500">
                        {user.email}
                      </p>
                    </div>
                  </div>
                </td>

                <td className="px-5 py-4">
                  <AdminStatusPill status={user.status} />
                </td>

                <td className="px-5 py-4 text-slate-700">{user.role}</td>
                <td className="px-5 py-4 text-slate-700">{user.department}</td>

                <td className="px-5 py-4">
                  <div className="text-slate-700">
                    {user.mfaEnabled ? "MFA enabled" : "MFA missing"}
                  </div>
                  <p className="mt-1 text-xs text-slate-500">
                    Risk: {user.riskLevel}
                  </p>
                </td>

                <td className="px-5 py-4 text-slate-700">
                  {user.activeSessions}
                </td>

                <td className="px-5 py-4 text-slate-500">
                  {user.lastActiveAt}
                </td>

                <td className="px-5 py-4 text-right">
                  <div className="flex justify-end gap-2">
                    <Button asChild variant="outline" size="sm">
                      <Link href={`/users/${user.id}`}>View</Link>
                    </Button>

                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button
                          variant="ghost"
                          size="icon"
                          aria-label={`Open actions for ${user.name}`}
                        >
                          <MoreHorizontal
                            className="size-4"
                            aria-hidden="true"
                          />
                        </Button>
                      </DropdownMenuTrigger>

                      <DropdownMenuContent align="end" className="w-56">
                        <DropdownMenuItem asChild>
                          <Link href={`/users/${user.id}`}>View profile</Link>
                        </DropdownMenuItem>
                        <DropdownMenuItem>Reset MFA</DropdownMenuItem>
                        <DropdownMenuItem>Revoke sessions</DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem className="text-red-600 focus:text-red-600">
                          Disable account
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
