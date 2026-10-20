"use client";

import * as React from "react";
import * as ProgressPrimitive from "@radix-ui/react-progress";
import { cn } from "../lib/utils";

const Progress = React.forwardRef<
  React.ComponentRef<typeof ProgressPrimitive.Root>,
  React.ComponentPropsWithoutRef<typeof ProgressPrimitive.Root>
>(({ className, value, max = 100, ...props }, ref) => {
  const maximum = Number.isFinite(max) && max > 0 ? max : 100;
  const current =
    typeof value === "number" && Number.isFinite(value)
      ? Math.min(maximum, Math.max(0, value))
      : null;
  return (
    <ProgressPrimitive.Root
      ref={ref}
      value={current}
      max={maximum}
      className={cn(
        "relative h-2 w-full overflow-hidden rounded-full bg-primary/12",
        className,
      )}
      {...props}
    >
      <progress
        aria-hidden="true"
        max={maximum}
        value={current ?? undefined}
        className="block h-full w-full appearance-none border-0 bg-transparent [&::-webkit-progress-bar]:bg-transparent [&::-webkit-progress-value]:bg-primary [&::-moz-progress-bar]:bg-primary"
      />
    </ProgressPrimitive.Root>
  );
});
Progress.displayName = ProgressPrimitive.Root.displayName;

export { Progress };
