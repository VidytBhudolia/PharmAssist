import * as React from "react";
import { cn } from "@/lib/utils";

/**
 * Avatar Component - Enterprise Design System
 *
 * User/entity representation with multiple sizes
 * Inspired by: Notion, Vercel, Google Cloud Console
 */
const Avatar = React.forwardRef(
  ({ className, children, size = "default", status, ...props }, ref) => {
    const sizes = {
      xs: "h-5 w-5 text-2xs",
      sm: "h-6 w-6 text-xs",
      default: "h-8 w-8 text-sm",
      lg: "h-10 w-10 text-base",
      xl: "h-12 w-12 text-lg",
    };

    const statusColors = {
      online: "bg-success-500",
      offline: "bg-slate-400",
      busy: "bg-danger-500",
      away: "bg-warning-500",
    };

    const statusSizes = {
      xs: "h-1.5 w-1.5 border",
      sm: "h-2 w-2 border",
      default: "h-2.5 w-2.5 border-2",
      lg: "h-3 w-3 border-2",
      xl: "h-3.5 w-3.5 border-2",
    };

    return (
      <div className="relative inline-block">
        <div
          ref={ref}
          className={cn(
            "relative flex shrink-0 overflow-hidden rounded-full",
            "border border-border bg-muted",
            "font-medium text-muted-foreground",
            sizes[size],
            className,
          )}
          {...props}
        >
          {children}
        </div>
        {status && (
          <span
            className={cn(
              "absolute bottom-0 right-0 rounded-full border-background",
              statusColors[status],
              statusSizes[size],
            )}
          />
        )}
      </div>
    );
  },
);
Avatar.displayName = "Avatar";

const AvatarImage = React.forwardRef(({ className, alt, ...props }, ref) => (
  <img ref={ref} alt={alt} className={cn("h-full w-full object-cover", className)} {...props} />
));
AvatarImage.displayName = "AvatarImage";

const AvatarFallback = React.forwardRef(({ className, children, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("flex h-full w-full items-center justify-center bg-muted uppercase", className)}
    {...props}
  >
    {children}
  </div>
));
AvatarFallback.displayName = "AvatarFallback";

/**
 * AvatarGroup - Stack multiple avatars
 */
const AvatarGroup = React.forwardRef(
  ({ className, children, max = 3, size = "default", ...props }, ref) => {
    const childArray = React.Children.toArray(children);
    const visibleChildren = childArray.slice(0, max);
    const remainingCount = childArray.length - max;

    const sizes = {
      xs: "h-5 w-5 text-2xs -ml-1",
      sm: "h-6 w-6 text-xs -ml-1.5",
      default: "h-8 w-8 text-sm -ml-2",
      lg: "h-10 w-10 text-base -ml-2.5",
      xl: "h-12 w-12 text-lg -ml-3",
    };

    return (
      <div ref={ref} className={cn("flex items-center", className)} {...props}>
        {visibleChildren.map((child, index) => (
          <div
            key={index}
            className={cn(
              "relative rounded-full ring-2 ring-background",
              index > 0 && sizes[size].split(" ").pop(),
            )}
          >
            {child}
          </div>
        ))}
        {remainingCount > 0 && (
          <div
            className={cn(
              "flex items-center justify-center rounded-full ring-2 ring-background",
              "bg-muted text-muted-foreground font-medium",
              sizes[size],
            )}
          >
            +{remainingCount}
          </div>
        )}
      </div>
    );
  },
);
AvatarGroup.displayName = "AvatarGroup";

export { Avatar, AvatarImage, AvatarFallback, AvatarGroup };
