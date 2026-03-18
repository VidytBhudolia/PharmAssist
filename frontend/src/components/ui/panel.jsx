import * as React from "react";
import { cn } from "@/lib/utils";

/**
 * Panel Component System - Enterprise Design System
 *
 * Structured containers for complex dashboard layouts
 * Inspired by: Palantir Foundry, Google Cloud Console, Notion
 */

const Panel = React.forwardRef(({ className, variant = "default", ...props }, ref) => {
  const variants = {
    default: "bg-card border border-border rounded",
    elevated: "bg-card border border-border rounded-md shadow-md",
    outlined: "bg-transparent border border-border rounded",
    filled: "bg-muted/50 border-0 rounded",
    glass: "bg-card/60 backdrop-blur-md border border-border/50 rounded-md",
    inset: "bg-surface-sunken border border-border rounded",
  };

  return <div ref={ref} className={cn(variants[variant], className)} {...props} />;
});
Panel.displayName = "Panel";

const PanelHeader = React.forwardRef(
  ({ className, title, description, action, compact = false, children, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        "flex items-start justify-between border-b border-border",
        compact ? "px-3 py-2" : "px-4 py-3",
        className,
      )}
      {...props}
    >
      <div className="flex-1 min-w-0">
        {title && (
          <h3
            className={cn(
              "font-medium text-foreground truncate",
              compact ? "text-sm" : "text-base",
            )}
          >
            {title}
          </h3>
        )}
        {description && (
          <p className="text-xs text-muted-foreground mt-0.5 truncate">{description}</p>
        )}
        {children}
      </div>
      {action && <div className="ml-3 flex-shrink-0">{action}</div>}
    </div>
  ),
);
PanelHeader.displayName = "PanelHeader";

const PanelBody = React.forwardRef(
  ({ className, compact = false, noPadding = false, ...props }, ref) => (
    <div ref={ref} className={cn(noPadding ? "" : compact ? "p-3" : "p-4", className)} {...props} />
  ),
);
PanelBody.displayName = "PanelBody";

const PanelFooter = React.forwardRef(({ className, compact = false, ...props }, ref) => (
  <div
    ref={ref}
    className={cn(
      "flex items-center justify-end gap-2 border-t border-border",
      compact ? "px-3 py-2" : "px-4 py-3",
      className,
    )}
    {...props}
  />
));
PanelFooter.displayName = "PanelFooter";

const PanelSection = React.forwardRef(
  (
    { className, title, description, collapsible = false, defaultOpen = true, children, ...props },
    ref,
  ) => {
    const [isOpen, setIsOpen] = React.useState(defaultOpen);

    return (
      <div ref={ref} className={cn("border-b border-border last:border-b-0", className)} {...props}>
        {(title || description) && (
          <div
            className={cn(
              "px-4 py-2 bg-muted/30",
              collapsible && "cursor-pointer hover:bg-muted/50 transition-colors",
            )}
            onClick={collapsible ? () => setIsOpen(!isOpen) : undefined}
          >
            <div className="flex items-center justify-between">
              <div>
                {title && (
                  <h4 className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                    {title}
                  </h4>
                )}
                {description && (
                  <p className="text-xs text-muted-foreground mt-0.5">{description}</p>
                )}
              </div>
              {collapsible && (
                <svg
                  className={cn(
                    "w-4 h-4 text-muted-foreground transition-transform",
                    isOpen && "rotate-180",
                  )}
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M19 9l-7 7-7-7"
                  />
                </svg>
              )}
            </div>
          </div>
        )}
        {(!collapsible || isOpen) && <div className="p-4">{children}</div>}
      </div>
    );
  },
);
PanelSection.displayName = "PanelSection";

/**
 * SplitPanel - Two-column layout for master-detail views
 */
const SplitPanel = React.forwardRef(
  ({ className, left, right, leftWidth = "w-1/3", resizable = false, ...props }, ref) => {
    return (
      <div ref={ref} className={cn("flex h-full", className)} {...props}>
        <div className={cn("flex-shrink-0 border-r border-border overflow-auto", leftWidth)}>
          {left}
        </div>
        {resizable && (
          <div className="w-1 cursor-col-resize hover:bg-primary/20 transition-colors" />
        )}
        <div className="flex-1 overflow-auto">{right}</div>
      </div>
    );
  },
);
SplitPanel.displayName = "SplitPanel";

/**
 * EmptyState - Placeholder for empty panels
 */
const EmptyState = React.forwardRef(
  ({ className, icon, title, description, action, ...props }, ref) => (
    <div
      ref={ref}
      className={cn("flex flex-col items-center justify-center p-8 text-center", className)}
      {...props}
    >
      {icon && (
        <div className="w-12 h-12 rounded-full bg-muted flex items-center justify-center text-muted-foreground mb-4">
          {icon}
        </div>
      )}
      {title && <h3 className="text-sm font-medium text-foreground mb-1">{title}</h3>}
      {description && <p className="text-xs text-muted-foreground max-w-sm mb-4">{description}</p>}
      {action}
    </div>
  ),
);
EmptyState.displayName = "EmptyState";

export { Panel, PanelHeader, PanelBody, PanelFooter, PanelSection, SplitPanel, EmptyState };
