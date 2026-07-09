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

export function UserMenu() {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button aria-label="Open user menu">
          <Avatar>
            <AvatarFallback>KA</AvatarFallback>
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
        <DropdownMenuItem>Sign out</DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
