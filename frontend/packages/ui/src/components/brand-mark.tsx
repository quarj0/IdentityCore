import * as React from "react";
import { Fingerprint } from "lucide-react";
import { cn } from "../lib/utils";

interface BrandMarkProps {
  subtitle?: string;
  size?: "sm" | "md" | "lg";
  variant?: "default" | "sidebar";
  className?: string;
}

const sizeConfig = {
  sm: { icon: "h-7 w-7", iconInner: "h-3.5 w-3.5", title: "text-xs", subtitle: "text-[10px]" },
  md: { icon: "h-8 w-8", iconInner: "h-4 w-4", title: "text-sm", subtitle: "text-xs" },
  lg: { icon: "h-9 w-9", iconInner: "h-4 w-4", title: "text-sm", subtitle: "text-xs" },
};

export function BrandMark({
  subtitle,
  size = "md",
  variant = "default",
  className,
}: BrandMarkProps) {
  const config = sizeConfig[size];
  const isSidebar = variant === "sidebar";

  return (
    <div className={cn("flex items-center gap-2.5", className)}>
      <div
        className={cn(
          "flex shrink-0 items-center justify-center rounded-md",
          config.icon,
          isSidebar
            ? "bg-sidebar-primary text-sidebar-primary-foreground"
            : "bg-primary text-primary-foreground"
        )}
      >
        <Fingerprint className={config.iconInner} strokeWidth={2} />
      </div>
      <div className="min-w-0">
        <div
          className={cn(
            "font-semibold tracking-tight",
            config.title,
            isSidebar ? "text-sidebar-foreground" : "text-foreground"
          )}
        >
          IdentityCore
        </div>
        {subtitle ? (
          <div
            className={cn(
              config.subtitle,
              isSidebar ? "text-sidebar-muted-foreground" : "text-muted-foreground"
            )}
          >
            {subtitle}
          </div>
        ) : null}
      </div>
    </div>
  );
}
