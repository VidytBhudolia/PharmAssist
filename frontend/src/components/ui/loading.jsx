import * as React from "react";
import { cn } from "@/lib/utils";

/**
 * Skeleton & Loading Components - Enterprise Design System
 *
 * Loading states and placeholders for async content
 * Inspired by: Vercel, Notion, Google Cloud Console
 */

const Skeleton = React.forwardRef(({ className, variant = "default", ...props }, ref) => {
  const variants = {
    default: "bg-muted",
    shimmer: [
      "relative overflow-hidden bg-muted",
      "before:absolute before:inset-0 before:-translate-x-full",
      "before:animate-[shimmer_2s_infinite]",
      "before:bg-gradient-to-r before:from-transparent before:via-white/10 before:to-transparent",
    ].join(" "),
  };

  return (
    <div
      ref={ref}
      className={cn("animate-pulse rounded", variants[variant], className)}
      {...props}
    />
  );
});
Skeleton.displayName = "Skeleton";

/**
 * SkeletonText - Text placeholder with multiple lines
 */
const SkeletonText = React.forwardRef(({ className, lines = 3, ...props }, ref) => (
  <div ref={ref} className={cn("space-y-2", className)} {...props}>
    {Array.from({ length: lines }).map((_, i) => (
      <Skeleton key={i} className={cn("h-4", i === lines - 1 && "w-3/4")} />
    ))}
  </div>
));
SkeletonText.displayName = "SkeletonText";

/**
 * SkeletonAvatar - Circular avatar placeholder
 */
const SkeletonAvatar = React.forwardRef(({ className, size = "default", ...props }, ref) => {
  const sizes = {
    sm: "h-6 w-6",
    default: "h-8 w-8",
    lg: "h-10 w-10",
    xl: "h-12 w-12",
  };

  return <Skeleton ref={ref} className={cn("rounded-full", sizes[size], className)} {...props} />;
});
SkeletonAvatar.displayName = "SkeletonAvatar";

/**
 * SkeletonCard - Card placeholder
 */
const SkeletonCard = React.forwardRef(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("bg-card border border-border rounded p-4 space-y-3", className)}
    {...props}
  >
    <div className="flex items-center gap-3">
      <SkeletonAvatar />
      <div className="space-y-1.5 flex-1">
        <Skeleton className="h-4 w-1/3" />
        <Skeleton className="h-3 w-1/4" />
      </div>
    </div>
    <SkeletonText lines={2} />
  </div>
));
SkeletonCard.displayName = "SkeletonCard";

/**
 * SkeletonTable - Table placeholder
 */
const SkeletonTable = React.forwardRef(({ className, rows = 5, columns = 4, ...props }, ref) => (
  <div ref={ref} className={cn("w-full", className)} {...props}>
    {/* Header */}
    <div className="flex gap-4 px-3 py-2 border-b border-border bg-muted/50">
      {Array.from({ length: columns }).map((_, i) => (
        <Skeleton key={i} className="h-4 flex-1" />
      ))}
    </div>
    {/* Rows */}
    {Array.from({ length: rows }).map((_, i) => (
      <div key={i} className="flex gap-4 px-3 py-3 border-b border-border">
        {Array.from({ length: columns }).map((_, j) => (
          <Skeleton key={j} className="h-4 flex-1" />
        ))}
      </div>
    ))}
  </div>
));
SkeletonTable.displayName = "SkeletonTable";

/**
 * Spinner - Loading spinner
 */
const Spinner = React.forwardRef(({ className, size = "default", ...props }, ref) => {
  const sizes = {
    xs: "h-3 w-3",
    sm: "h-4 w-4",
    default: "h-5 w-5",
    lg: "h-6 w-6",
    xl: "h-8 w-8",
  };

  return (
    <svg
      ref={ref}
      className={cn("animate-spin text-primary", sizes[size], className)}
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
      {...props}
    >
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
      />
    </svg>
  );
});
Spinner.displayName = "Spinner";

/**
 * LoadingDots - Animated loading dots
 */
const LoadingDots = React.forwardRef(({ className, ...props }, ref) => (
  <span ref={ref} className={cn("inline-flex gap-1", className)} {...props}>
    {[0, 1, 2].map((i) => (
      <span
        key={i}
        className="w-1.5 h-1.5 bg-current rounded-full animate-bounce"
        style={{ animationDelay: `${i * 0.15}s` }}
      />
    ))}
  </span>
));
LoadingDots.displayName = "LoadingDots";

/**
 * LoadingOverlay - Full container loading overlay
 */
const LoadingOverlay = React.forwardRef(({ className, message, ...props }, ref) => (
  <div
    ref={ref}
    className={cn(
      "absolute inset-0 flex flex-col items-center justify-center",
      "bg-background/80 backdrop-blur-sm z-50",
      className,
    )}
    {...props}
  >
    <Spinner size="lg" />
    {message && <p className="mt-3 text-sm text-muted-foreground">{message}</p>}
  </div>
));
LoadingOverlay.displayName = "LoadingOverlay";

/**
 * ProgressBar - Linear progress indicator
 */
const ProgressBar = React.forwardRef(
  (
    {
      className,
      value = 0,
      max = 100,
      size = "default",
      variant = "default",
      showLabel = false,
      indeterminate = false,
      ...props
    },
    ref,
  ) => {
    const percentage = Math.min(100, Math.max(0, (value / max) * 100));

    const sizes = {
      xs: "h-1",
      sm: "h-1.5",
      default: "h-2",
      lg: "h-3",
    };

    const variants = {
      default: "bg-primary",
      success: "bg-success-500",
      warning: "bg-warning-500",
      danger: "bg-danger-500",
    };

    return (
      <div ref={ref} className={cn("w-full", className)} {...props}>
        <div className={cn("w-full bg-muted rounded-full overflow-hidden", sizes[size])}>
          <div
            className={cn(
              "h-full rounded-full transition-all duration-300",
              variants[variant],
              indeterminate && "animate-[indeterminate_1.5s_ease-in-out_infinite]",
            )}
            style={{ width: indeterminate ? "40%" : `${percentage}%` }}
          />
        </div>
        {showLabel && !indeterminate && (
          <div className="flex justify-between mt-1 text-xs text-muted-foreground">
            <span>{value}</span>
            <span>{max}</span>
          </div>
        )}
      </div>
    );
  },
);
ProgressBar.displayName = "ProgressBar";

export {
  Skeleton,
  SkeletonText,
  SkeletonAvatar,
  SkeletonCard,
  SkeletonTable,
  Spinner,
  LoadingDots,
  LoadingOverlay,
  ProgressBar,
};
