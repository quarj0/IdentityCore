"use client";

import {
  Bell,
  ChevronDown,
  Search,
} from "lucide-react";
import {
  Avatar,
  AvatarFallback,
  AvatarImage,
  Button,
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
  Input,
  Separator,
} from "@identitycore/ui";

export function Topbar() {
  return (
    <header className="sticky top-0 z-30 flex h-14 shrink-0 items-center gap-3 border-b border-border bg-background px-4 lg:px-6">
      <div className="relative hidden flex-1 md:block md:max-w-sm">
        <Search className="absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          placeholder="Search..."
          className="h-9 bg-muted/50 pl-9 text-sm"
          id="topbar-search"
        />
      </div>

      <div className="flex-1 md:hidden" />

      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="outline" size="sm" className="hidden h-9 gap-2 sm:flex">
            Acme Corp
            <ChevronDown className="h-3.5 w-3.5 text-muted-foreground" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          <DropdownMenuItem>Switch workspace</DropdownMenuItem>
          <DropdownMenuItem>Create workspace</DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>

      <Separator orientation="vertical" className="hidden h-5 sm:block" />

      <Button variant="ghost" size="icon" className="relative h-9 w-9" id="topbar-notifications">
        <Bell className="h-4 w-4" />
        <span className="absolute right-2 top-2 h-1.5 w-1.5 rounded-full bg-destructive" />
        <span className="sr-only">Notifications</span>
      </Button>

      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost" id="topbar-user-menu" className="h-9 gap-2 px-2">
            <Avatar className="h-7 w-7">
              <AvatarImage src="" alt="User avatar" />
              <AvatarFallback className="bg-muted text-xs">AC</AvatarFallback>
            </Avatar>
            <ChevronDown className="hidden h-3.5 w-3.5 text-muted-foreground sm:block" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-56">
          <DropdownMenuLabel className="font-normal">
            <div className="flex flex-col space-y-1">
              <p className="text-sm font-medium">Acme Corporation</p>
              <p className="text-xs text-muted-foreground">admin@acme.com</p>
            </div>
          </DropdownMenuLabel>
          <DropdownMenuSeparator />
          <DropdownMenuItem id="menu-profile">Profile</DropdownMenuItem>
          <DropdownMenuItem id="menu-settings">Settings</DropdownMenuItem>
          <DropdownMenuItem id="menu-billing">Billing</DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuItem id="menu-signout" className="text-destructive">
            Sign out
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </header>
  );
}
