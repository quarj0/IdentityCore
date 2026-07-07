"use client";

import React from "react";
import { Bell, Search, Sun, Moon, ChevronDown } from "lucide-react";
import {
  Button,
  Avatar,
  AvatarFallback,
  AvatarImage,
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
  Input,
} from "@identitycore/ui";

interface TopbarProps {
  breadcrumb?: { label: string; href?: string }[];
}

export function Topbar({ breadcrumb = [] }: TopbarProps) {
  return (
    <header className="flex h-[60px] shrink-0 items-center gap-4 border-b border-border bg-background px-6">
      {/* Breadcrumb */}
      <div className="flex items-center gap-1.5 text-sm">
        {breadcrumb.map((crumb, i) => (
          <React.Fragment key={i}>
            {i > 0 && (
              <span className="text-muted-foreground/50">/</span>
            )}
            <span
              className={
                i === breadcrumb.length - 1
                  ? "font-medium text-foreground"
                  : "text-muted-foreground"
              }
            >
              {crumb.label}
            </span>
          </React.Fragment>
        ))}
      </div>

      {/* Spacer */}
      <div className="flex-1" />

      {/* Search */}
      <div className="relative hidden md:block">
        <Search className="absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
        <Input
          placeholder="Search..."
          className="h-8 w-56 pl-8 text-xs bg-muted/50 border-border/60"
          id="topbar-search"
        />
      </div>

      {/* Notifications */}
      <Button variant="ghost" size="icon" className="relative h-8 w-8" id="topbar-notifications">
        <Bell className="h-4 w-4" />
        {/* notification dot */}
        <span className="absolute right-1.5 top-1.5 h-1.5 w-1.5 rounded-full bg-destructive" />
        <span className="sr-only">Notifications</span>
      </Button>

      {/* User menu */}
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button
            variant="ghost"
            id="topbar-user-menu"
            className="flex h-8 items-center gap-2 rounded-md px-2 hover:bg-accent"
          >
            <Avatar className="h-6 w-6">
              <AvatarImage src="" alt="User avatar" />
              <AvatarFallback className="text-xs bg-primary text-primary-foreground">
                AC
              </AvatarFallback>
            </Avatar>
            <span className="hidden text-sm font-medium sm:block">Acme Corp</span>
            <ChevronDown className="h-3.5 w-3.5 text-muted-foreground" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-52">
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
