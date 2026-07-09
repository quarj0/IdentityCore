"use client";

import Link from "next/link";
import { MoreHorizontal, RotateCcw, ShieldOff, Trash2 } from "lucide-react";
import {
  Button,
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@identitycore/ui";
import type { Organization } from "@/features/organizations/mock-data";

type OrganizationActionsMenuProps = {
  organization: Organization;
};

export function OrganizationActionsMenu({
  organization,
}: OrganizationActionsMenuProps) {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          aria-label={`Open actions for ${organization.name}`}
          className="text-slate-400 hover:bg-white/10 hover:text-white"
        >
          <MoreHorizontal className="size-4" aria-hidden="true" />
        </Button>
      </DropdownMenuTrigger>

      <DropdownMenuContent align="end" className="w-56">
        <DropdownMenuItem asChild>
          <Link href={`/organizations/${organization.id}`}>
            View organization
          </Link>
        </DropdownMenuItem>

        <DropdownMenuItem>View usage</DropdownMenuItem>
        <DropdownMenuItem>View audit trail</DropdownMenuItem>

        <DropdownMenuSeparator />

        {organization.status === "suspended" ? (
          <DropdownMenuItem>
            <RotateCcw className="mr-2 size-4" aria-hidden="true" />
            Reactivate
          </DropdownMenuItem>
        ) : (
          <DropdownMenuItem>
            <ShieldOff className="mr-2 size-4" aria-hidden="true" />
            Suspend
          </DropdownMenuItem>
        )}

        <DropdownMenuItem className="text-rose-600 focus:text-rose-600">
          <Trash2 className="mr-2 size-4" aria-hidden="true" />
          Delete organization
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
