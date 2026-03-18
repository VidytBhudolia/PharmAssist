import * as React from "react";
import { cn } from "@/lib/utils";

/**
 * Card Component System - Enterprise Design System
 *
 * Layered surface components for information hierarchy
 * Inspired by: Palantir Foundry, Notion Enterprise, Google Cloud Console
 */

const Card = React.forwardRef(({ className, variant = "default", ...props }, ref) => {
  const variants = {
    default: "bg-card border border-border rounded shadow-sm",
    elevated: "bg-card border border-border rounded-md shadow-md",
    outline: "bg-transparent border border-border rounded",
    ghost: "bg-transparent",
    filled: "bg-muted border-0 rounded",
    glass: "bg-card/80 backdrop-blur-sm border border-border/50 rounded-md shadow-sm",
  };

  return (
    <div
      ref={ref}
      className={cn("text-card-foreground", variants[variant], className)}
      {...props}
    />
  );
});
Card.displayName = "Card";

const CardHeader = React.forwardRef(({ className, compact = false, ...props }, ref) => (
  <div
    ref={ref}
    className={cn(
      "flex flex-col border-b border-border",
      compact ? "px-3 py-2 space-y-0.5" : "px-4 py-3 space-y-1",
      className,
    )}
    {...props}
  />
));
CardHeader.displayName = "CardHeader";

const CardTitle = React.forwardRef(({ className, size = "default", ...props }, ref) => {
  const sizes = {
    sm: "text-sm font-medium leading-tight",
    default: "text-base font-semibold leading-tight tracking-tight",
    lg: "text-lg font-semibold leading-tight tracking-tight",
  };

  return <h3 ref={ref} className={cn(sizes[size], className)} {...props} />;
});
CardTitle.displayName = "CardTitle";

const CardDescription = React.forwardRef(({ className, ...props }, ref) => (
  <p
    ref={ref}
    className={cn("text-xs text-muted-foreground leading-normal", className)}
    {...props}
  />
));
CardDescription.displayName = "CardDescription";

const CardContent = React.forwardRef(({ className, compact = false, ...props }, ref) => (
  <div ref={ref} className={cn(compact ? "px-3 py-2" : "px-4 py-3", className)} {...props} />
));
CardContent.displayName = "CardContent";

const CardFooter = React.forwardRef(({ className, compact = false, ...props }, ref) => (
  <div
    ref={ref}
    className={cn(
      "flex items-center border-t border-border",
      compact ? "px-3 py-2 gap-2" : "px-4 py-3 gap-3",
      className,
    )}
    {...props}
  />
));
CardFooter.displayName = "CardFooter";

/**
 * CardSection - Divides card content into logical sections
 */
const CardSection = React.forwardRef(
  ({ className, title, description, children, ...props }, ref) => (
    <div
      ref={ref}
      className={cn("py-3 border-b border-border last:border-b-0", className)}
      {...props}
    >
      {(title || description) && (
        <div className="mb-2">
          {title && <h4 className="text-sm font-medium text-foreground">{title}</h4>}
          {description && <p className="text-xs text-muted-foreground mt-0.5">{description}</p>}
        </div>
      )}
      {children}
    </div>
  ),
);
CardSection.displayName = "CardSection";

/**
 * CardMetric - Display key metrics/KPIs
 */
const CardMetric = React.forwardRef(
  ({ className, label, value, change, changeType = "neutral", ...props }, ref) => {
    const changeColors = {
      positive: "text-success-600",
      negative: "text-danger-600",
      neutral: "text-muted-foreground",
    };

    return (
      <div ref={ref} className={cn("space-y-1", className)} {...props}>
        <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
          {label}
        </p>
        <p className="text-2xl font-semibold tabular-nums">{value}</p>
        {change && <p className={cn("text-xs font-medium", changeColors[changeType])}>{change}</p>}
      </div>
    );
  },
);
CardMetric.displayName = "CardMetric";

export {
  Card,
  CardHeader,
  CardFooter,
  CardTitle,
  CardDescription,
  CardContent,
  CardSection,
  CardMetric,
};
