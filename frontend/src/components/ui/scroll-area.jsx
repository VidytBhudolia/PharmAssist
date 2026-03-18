import * as React from "react";
import { cn } from "@/lib/utils";

/**
 * ScrollArea Component - Enterprise Design System
 *
 * Custom scrollable container with styled scrollbars
 * Supports both vertical and horizontal scrolling
 */
const ScrollArea = React.forwardRef(
  ({ className, children, orientation = "vertical", hideScrollbar = false, ...props }, ref) => {
    const orientationClasses = {
      vertical: "overflow-y-auto overflow-x-hidden",
      horizontal: "overflow-x-auto overflow-y-hidden",
      both: "overflow-auto",
    };

    return (
      <div ref={ref} className={cn("relative", className)} {...props}>
        <div
          className={cn(
            "h-full w-full",
            orientationClasses[orientation],
            hideScrollbar
              ? "scrollbar-none"
              : [
                  "scrollbar-thin",
                  "scrollbar-track-transparent",
                  "scrollbar-thumb-slate-300 dark:scrollbar-thumb-slate-700",
                  "hover:scrollbar-thumb-slate-400 dark:hover:scrollbar-thumb-slate-600",
                  "scrollbar-thumb-rounded-full",
                ].join(" "),
          )}
          style={{ scrollbarGutter: hideScrollbar ? undefined : "stable" }}
        >
          {children}
        </div>
      </div>
    );
  },
);
ScrollArea.displayName = "ScrollArea";

/**
 * ScrollAreaViewport - For more complex scroll area needs
 */
const ScrollAreaViewport = React.forwardRef(({ className, children, ...props }, ref) => (
  <div
    ref={ref}
    className={cn(
      "h-full w-full rounded-[inherit]",
      "overflow-y-auto overflow-x-hidden",
      "scrollbar-thin scrollbar-track-transparent",
      "scrollbar-thumb-slate-300 dark:scrollbar-thumb-slate-700",
      "hover:scrollbar-thumb-slate-400 dark:hover:scrollbar-thumb-slate-600",
      "scrollbar-thumb-rounded-full",
      className,
    )}
    {...props}
  >
    {children}
  </div>
));
ScrollAreaViewport.displayName = "ScrollAreaViewport";

export { ScrollArea, ScrollAreaViewport };
