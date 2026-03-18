import * as React from "react";
import { cn } from "@/lib/utils";

/**
 * Input Component - Enterprise Design System
 *
 * Clean, accessible form controls with multiple sizes
 * Inspired by: Vercel Dashboard, Notion, Google Cloud Console
 */
const Input = React.forwardRef(
  (
    {
      className,
      type = "text",
      size = "default",
      variant = "default",
      leftIcon,
      rightIcon,
      error,
      ...props
    },
    ref,
  ) => {
    const sizes = {
      sm: "h-7 px-2.5 text-xs",
      default: "h-8 px-3 text-sm",
      lg: "h-9 px-3 text-sm",
      xl: "h-10 px-4 text-base",
    };

    const variants = {
      default: [
        "bg-background border border-input",
        "focus-visible:border-ring focus-visible:ring-2 focus-visible:ring-ring/20",
      ].join(" "),
      filled: [
        "bg-muted border border-transparent",
        "focus-visible:bg-background focus-visible:border-ring focus-visible:ring-2 focus-visible:ring-ring/20",
      ].join(" "),
      ghost: ["bg-transparent border-0", "focus-visible:bg-muted"].join(" "),
    };

    const hasLeftIcon = !!leftIcon;
    const hasRightIcon = !!rightIcon;

    const inputElement = (
      <input
        type={type}
        className={cn(
          "flex w-full rounded transition-colors duration-150",
          "text-foreground placeholder:text-muted-foreground",
          "focus-visible:outline-none",
          "disabled:cursor-not-allowed disabled:opacity-50",
          "file:border-0 file:bg-transparent file:text-sm file:font-medium file:text-foreground",
          sizes[size],
          variants[variant],
          error &&
            "border-danger-500 focus-visible:border-danger-500 focus-visible:ring-danger-500/20",
          hasLeftIcon && "pl-9",
          hasRightIcon && "pr-9",
          className,
        )}
        ref={ref}
        {...props}
      />
    );

    if (hasLeftIcon || hasRightIcon) {
      return (
        <div className="relative">
          {hasLeftIcon && (
            <div className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground pointer-events-none [&_svg]:size-4">
              {leftIcon}
            </div>
          )}
          {inputElement}
          {hasRightIcon && (
            <div className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground [&_svg]:size-4">
              {rightIcon}
            </div>
          )}
        </div>
      );
    }

    return inputElement;
  },
);
Input.displayName = "Input";

/**
 * Textarea Component
 */
const Textarea = React.forwardRef(({ className, variant = "default", error, ...props }, ref) => {
  const variants = {
    default: [
      "bg-background border border-input",
      "focus-visible:border-ring focus-visible:ring-2 focus-visible:ring-ring/20",
    ].join(" "),
    filled: [
      "bg-muted border border-transparent",
      "focus-visible:bg-background focus-visible:border-ring focus-visible:ring-2 focus-visible:ring-ring/20",
    ].join(" "),
  };

  return (
    <textarea
      className={cn(
        "flex w-full min-h-[80px] px-3 py-2 rounded text-sm",
        "text-foreground placeholder:text-muted-foreground",
        "transition-colors duration-150 resize-y",
        "focus-visible:outline-none",
        "disabled:cursor-not-allowed disabled:opacity-50",
        variants[variant],
        error &&
          "border-danger-500 focus-visible:border-danger-500 focus-visible:ring-danger-500/20",
        className,
      )}
      ref={ref}
      {...props}
    />
  );
});
Textarea.displayName = "Textarea";

/**
 * InputGroup - Wrapper for inputs with labels and helpers
 */
const InputGroup = React.forwardRef(
  ({ className, label, description, error, required, children, ...props }, ref) => {
    return (
      <div ref={ref} className={cn("space-y-1.5", className)} {...props}>
        {label && (
          <label className="text-sm font-medium text-foreground">
            {label}
            {required && <span className="text-danger-500 ml-0.5">*</span>}
          </label>
        )}
        {description && <p className="text-xs text-muted-foreground">{description}</p>}
        {children}
        {error && <p className="text-xs text-danger-500">{error}</p>}
      </div>
    );
  },
);
InputGroup.displayName = "InputGroup";

/**
 * SearchInput - Specialized search input with icon
 */
const SearchInput = React.forwardRef(({ className, ...props }, ref) => {
  return (
    <div className="relative">
      <svg
        className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground pointer-events-none"
        width="14"
        height="14"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <circle cx="11" cy="11" r="8" />
        <line x1="21" y1="21" x2="16.65" y2="16.65" />
      </svg>
      <input
        type="search"
        className={cn(
          "flex h-8 w-full pl-9 pr-3 rounded text-sm",
          "bg-muted border border-transparent",
          "text-foreground placeholder:text-muted-foreground",
          "transition-colors duration-150",
          "focus-visible:outline-none focus-visible:bg-background focus-visible:border-ring focus-visible:ring-2 focus-visible:ring-ring/20",
          "disabled:cursor-not-allowed disabled:opacity-50",
          className,
        )}
        ref={ref}
        {...props}
      />
    </div>
  );
});
SearchInput.displayName = "SearchInput";

export { Input, Textarea, InputGroup, SearchInput };
