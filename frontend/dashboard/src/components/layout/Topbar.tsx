"use client";

import React from "react";
import { Bell, ChevronDown, Search, Sparkles } from "lucide-react";
import {
  Avatar,
  AvatarFallback,
  AvatarImage,
  Badge,
  Button,
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
  const currentLabel = breadcrumb.at(-1)?.label ?? "Overview";

  return (
    <header className="sticky top-0 z-30 px-4 pt-4 md:px-6">
      <div className="flex h-[72px] items-center gap-4 rounded-[1.75rem] border border-border/70 bg-background/76 px-6 shadow-[0_24px_80px_-52px_rgba(15,23,42,0.45)] backdrop-blur-xl">
        <div className="min-w-0">
          <div className="flex items-center gap-1.5 text-sm">
            {breadcrumb.map((crumb, index) => (
              <React.Fragment key={`${crumb.label}-${index}`}>
                {index > 0 ? <span className="text-muted-foreground/50">/</span> : null}
                <span
                  className={
                    index === breadcrumb.length - 1
                      ? "font-medium text-foreground"
                      : "text-muted-foreground"
                  }
                >
                  {crumb.label}
                </span>
              </React.Fragment>
            ))}
          </div>
          <div className="mt-1 flex items-center gap-2">
            <h1 className="text-lg font-semibold tracking-tight text-foreground">
              {currentLabel}
            </h1>
            <Badge variant="secondary" className="hidden sm:inline-flex">
              <Sparkles className="h-3 w-3" />
              Healthy workspace
            </Badge>
          </div>
        </div>

        <div className="flex-1" />

        <div className="relative hidden md:block">
          <Search className="absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search requests, subjects, keys..."
            className="h-10 w-72 pl-9 text-sm"
            id="topbar-search"
          />
        </div>

        <Button
          variant="ghost"
          size="icon"
          className="relative h-10 w-10 rounded-xl"
          id="topbar-notifications"
        >
          <Bell className="h-4 w-4" />
          <span className="absolute right-2 top-2 h-1.5 w-1.5 rounded-full bg-destructive" />
          <span className="sr-only">Notifications</span>
        </Button>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              id="topbar-user-menu"
              className="flex h-11 items-center gap-2 rounded-xl px-2 hover:bg-accent"
            >
              <Avatar className="h-8 w-8">
                <AvatarImage src="" alt="User avatar" />
                <AvatarFallback className="text-xs bg-primary text-primary-foreground">
                  AC
                </AvatarFallback>
              </Avatar>
              <span className="hidden text-sm font-medium sm:block">Acme Corp</span>
              <ChevronDown className="h-3.5 w-3.5 text-muted-foreground" />
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
      </div>
    </header>
  );
}
