import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "../lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-xl text-sm font-semibold transition-[transform,box-shadow,background-color,border-color,color] duration-200 ease-out focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 disabled:shadow-none [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0",
  {
    variants: {
      variant: {
        default:
          "border border-primary/80 bg-linear-to-r from-primary via-primary to-primary/85 text-primary-foreground shadow-[0_14px_30px_-18px_hsl(var(--primary)/0.85)] hover:-translate-y-0.5 hover:shadow-[0_18px_40px_-18px_hsl(var(--primary)/0.9)] active:translate-y-0",
        destructive:
          "border border-destructive/80 bg-destructive text-destructive-foreground shadow-[0_14px_28px_-20px_hsl(var(--destructive)/0.9)] hover:-translate-y-0.5 hover:bg-destructive/92 active:translate-y-0",
        outline:
          "border border-border/80 bg-background/88 text-foreground shadow-[0_12px_24px_-24px_rgba(15,23,42,0.5)] backdrop-blur-sm hover:-translate-y-0.5 hover:border-primary/30 hover:bg-accent/60 hover:text-accent-foreground",
        secondary:
          "border border-secondary/70 bg-secondary/90 text-secondary-foreground shadow-[0_10px_24px_-24px_rgba(15,23,42,0.6)] hover:-translate-y-0.5 hover:bg-secondary",
        ghost:
          "text-foreground/76 hover:bg-accent/70 hover:text-accent-foreground",
        link: "text-primary underline-offset-4 hover:underline",
      },
      size: {
        default: "h-10 px-4 py-2.5",
        sm: "h-8 rounded-lg px-3 text-xs",
        lg: "h-11 rounded-xl px-6 text-sm",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    );
  }
);
Button.displayName = "Button";

export { Button, buttonVariants };
