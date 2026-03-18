import * as React from "react";
import { cva } from "class-variance-authority";
import { cn } from "@/lib/utils";

/**
 * Badge Component - Enterprise Design System
 *
 * Status indicators, labels, and tags for clinical data
 * Inspired by: Benchling, Palantir Foundry, Google Cloud Console
 */
const badgeVariants = cva(
  ["inline-flex items-center gap-1 font-medium transition-colors", "border rounded-sm"].join(" "),
  {
    variants: {
      variant: {
        // Default - Neutral
        default: "bg-secondary text-secondary-foreground border-transparent",

        // Primary - Clinical blue
        primary:
          "bg-clinical-500/10 text-clinical-600 dark:text-clinical-400 border-clinical-500/20",

        // Success - Positive outcomes
        success: "bg-success-500/10 text-success-700 dark:text-success-400 border-success-500/20",

        // Warning - Caution
        warning: "bg-warning-500/10 text-warning-700 dark:text-warning-400 border-warning-500/20",

        // Danger - Critical/Error
        danger: "bg-danger-500/10 text-danger-600 dark:text-danger-400 border-danger-500/20",

        // Info - Informational
        info: "bg-data-500/10 text-data-700 dark:text-data-400 border-data-500/20",

        // Insight - AI/Analytics
        insight: "bg-insight-500/10 text-insight-600 dark:text-insight-400 border-insight-500/20",

        // Outline variants
        "outline-default": "bg-transparent text-foreground border-border",
        "outline-primary":
          "bg-transparent text-clinical-600 dark:text-clinical-400 border-clinical-500/50",
        "outline-success":
          "bg-transparent text-success-600 dark:text-success-400 border-success-500/50",
        "outline-warning":
          "bg-transparent text-warning-600 dark:text-warning-400 border-warning-500/50",
        "outline-danger":
          "bg-transparent text-danger-600 dark:text-danger-400 border-danger-500/50",
      },
      size: {
        sm: "px-1.5 py-0.5 text-2xs",
        default: "px-2 py-0.5 text-xs",
        lg: "px-2.5 py-1 text-xs",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  },
);

const Badge = React.forwardRef(
  ({ className, variant, size, dot, removable, onRemove, children, ...props }, ref) => {
    return (
      <span ref={ref} className={cn(badgeVariants({ variant, size }), className)} {...props}>
        {dot && (
          <span
            className={cn(
              "w-1.5 h-1.5 rounded-full",
              variant === "success" && "bg-success-500",
              variant === "warning" && "bg-warning-500",
              variant === "danger" && "bg-danger-500",
              variant === "info" && "bg-data-500",
              variant === "primary" && "bg-clinical-500",
              variant === "insight" && "bg-insight-500",
              (!variant || variant === "default") && "bg-slate-400",
            )}
          />
        )}
        {children}
        {removable && (
          <button
            type="button"
            onClick={onRemove}
            className="ml-0.5 -mr-0.5 p-0.5 rounded-sm hover:bg-foreground/10 transition-colors"
          >
            <svg
              width="10"
              height="10"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.5"
            >
              <path d="M18 6L6 18M6 6l12 12" />
            </svg>
          </button>
        )}
      </span>
    );
  },
);
Badge.displayName = "Badge";

/**
 * StatusBadge - Specialized badge for status indicators
 */
const StatusBadge = React.forwardRef(
  ({ className, status = "default", children, ...props }, ref) => {
    const statusConfig = {
      default: { variant: "default", label: "Unknown" },
      active: { variant: "success", label: "Active" },
      inactive: { variant: "default", label: "Inactive" },
      pending: { variant: "warning", label: "Pending" },
      error: { variant: "danger", label: "Error" },
      processing: { variant: "primary", label: "Processing" },
      completed: { variant: "success", label: "Completed" },
      draft: { variant: "default", label: "Draft" },
      review: { variant: "info", label: "In Review" },
      approved: { variant: "success", label: "Approved" },
      rejected: { variant: "danger", label: "Rejected" },
    };

    const config = statusConfig[status] || statusConfig.default;

    return (
      <Badge ref={ref} variant={config.variant} dot className={className} {...props}>
        {children || config.label}
      </Badge>
    );
  },
);
StatusBadge.displayName = "StatusBadge";

export { Badge, StatusBadge, badgeVariants };
