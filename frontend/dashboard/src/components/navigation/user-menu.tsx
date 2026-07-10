"use client";

import Link from "next/link";
import {
  Avatar,
  AvatarFallback,
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@identitycore/ui";
import { useDashboardSession } from "@/components/auth/dashboard-session";

export function UserMenu() {
  const { logout, user } = useDashboardSession();
  const initials = (user?.full_name || user?.email || "User")
    .split(/\s|@/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join("") || "U";

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button aria-label="Open user menu">
          <Avatar>
            <AvatarFallback>{initials}</AvatarFallback>
          </Avatar>
        </button>
      </DropdownMenuTrigger>

      <DropdownMenuContent align="end" className="w-56 rounded-2xl">
        <DropdownMenuItem asChild>
          <Link href="/settings/profile">Profile</Link>
        </DropdownMenuItem>
        <DropdownMenuItem asChild>
          <Link href="/settings">Workspace settings</Link>
        </DropdownMenuItem>
        <DropdownMenuItem asChild>
          <a href="http://localhost:3003">Developer portal</a>
        </DropdownMenuItem>
        <DropdownMenuItem asChild>
          <Link href="/billing">Billing</Link>
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => void logout()}>Sign out</DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
