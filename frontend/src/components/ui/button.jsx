import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva } from "class-variance-authority";

import { cn } from "@/lib/utils";

/**
 * Button Component - Enterprise Design System
 *
 * Clinical-grade button with multiple variants and sizes
 * Inspired by: Palantir Foundry, Vercel Dashboard, Benchling
 */
const buttonVariants = cva(
  [
    "inline-flex items-center justify-center gap-2 whitespace-nowrap",
    "font-medium transition-all duration-150 ease-out",
    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background",
    "disabled:pointer-events-none disabled:opacity-50",
    "[&_svg]:pointer-events-none [&_svg]:shrink-0",
  ].join(" "),
  {
    variants: {
      variant: {
        // Primary - Main actions (Clinical Blue)
        default: [
          "bg-primary text-primary-foreground",
          "shadow-sm hover:bg-primary/90 active:bg-primary/95",
          "border border-primary",
        ].join(" "),

        // Destructive - Danger actions
        destructive: [
          "bg-danger-500 text-white",
          "shadow-sm hover:bg-danger-600 active:bg-danger-700",
          "border border-danger-500",
        ].join(" "),

        // Outline - Bordered, transparent background
        outline: [
          "bg-transparent text-foreground",
          "border border-input hover:bg-accent hover:text-accent-foreground",
          "active:bg-accent/80",
        ].join(" "),

        // Secondary - Subtle emphasis
        secondary: [
          "bg-secondary text-secondary-foreground",
          "border border-border hover:bg-secondary/80",
          "active:bg-secondary/90",
        ].join(" "),

        // Ghost - Minimal, no background
        ghost: [
          "bg-transparent text-foreground",
          "hover:bg-accent hover:text-accent-foreground",
          "active:bg-accent/80",
        ].join(" "),

        // Link - Text only, underline on hover
        link: ["text-primary underline-offset-4", "hover:underline", "h-auto p-0"].join(" "),

        // Success - Positive actions
        success: [
          "bg-success-500 text-white",
          "shadow-sm hover:bg-success-600 active:bg-success-700",
          "border border-success-500",
        ].join(" "),

        // Warning - Caution actions
        warning: [
          "bg-warning-500 text-slate-900",
          "shadow-sm hover:bg-warning-600 active:bg-warning-700",
          "border border-warning-500",
        ].join(" "),
      },
      size: {
        // Extra small - Tags, badges, dense UIs
        xs: "h-6 px-2 text-xs rounded-sm [&_svg]:size-3",

        // Small - Secondary actions, compact layouts
        sm: "h-7 px-2.5 text-xs rounded-sm [&_svg]:size-3.5",

        // Default - Standard actions
        default: "h-8 px-3 text-sm rounded [&_svg]:size-4",

        // Large - Primary page actions
        lg: "h-9 px-4 text-sm rounded [&_svg]:size-4",

        // Extra large - Hero CTAs
        xl: "h-10 px-5 text-base rounded-md [&_svg]:size-5",

        // Icon only variants
        icon: "h-8 w-8 p-0 rounded [&_svg]:size-4",
        "icon-xs": "h-6 w-6 p-0 rounded-sm [&_svg]:size-3",
        "icon-sm": "h-7 w-7 p-0 rounded-sm [&_svg]:size-3.5",
        "icon-lg": "h-9 w-9 p-0 rounded [&_svg]:size-4",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  },
);

const Button = React.forwardRef(({ className, variant, size, asChild = false, ...props }, ref) => {
  const Comp = asChild ? Slot : "button";
  return <Comp className={cn(buttonVariants({ variant, size, className }))} ref={ref} {...props} />;
});
Button.displayName = "Button";

export { Button, buttonVariants };
