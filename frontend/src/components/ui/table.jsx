import * as React from "react";
import { cn } from "@/lib/utils";

/**
 * Table Component System - Enterprise Design System
 *
 * Dense, scannable data tables for research data
 * Inspired by: Palantir Foundry, Benchling, Google Cloud Console
 */

const Table = React.forwardRef(
  (
    { className, variant = "default", dense = false, striped = false, hoverable = true, ...props },
    ref,
  ) => {
    const variants = {
      default: "",
      bordered: "border border-border rounded-md overflow-hidden",
      card: "bg-card border border-border rounded-md shadow-sm overflow-hidden",
    };

    return (
      <div className={cn("w-full overflow-auto", variants[variant])}>
        <table
          ref={ref}
          data-dense={dense}
          data-striped={striped}
          data-hoverable={hoverable}
          className={cn("w-full text-sm caption-bottom", className)}
          {...props}
        />
      </div>
    );
  },
);
Table.displayName = "Table";

const TableHeader = React.forwardRef(({ className, ...props }, ref) => (
  <thead
    ref={ref}
    className={cn("bg-muted/50 border-b border-border", "[&_tr]:border-b-0", className)}
    {...props}
  />
));
TableHeader.displayName = "TableHeader";

const TableBody = React.forwardRef(({ className, ...props }, ref) => (
  <tbody
    ref={ref}
    className={cn(
      "[&_tr:last-child]:border-0",
      // Striped rows
      "[[data-striped=true]_&_tr:nth-child(even)]:bg-muted/30",
      className,
    )}
    {...props}
  />
));
TableBody.displayName = "TableBody";

const TableFooter = React.forwardRef(({ className, ...props }, ref) => (
  <tfoot
    ref={ref}
    className={cn("border-t border-border bg-muted/50 font-medium", className)}
    {...props}
  />
));
TableFooter.displayName = "TableFooter";

const TableRow = React.forwardRef(({ className, selected, ...props }, ref) => (
  <tr
    ref={ref}
    className={cn(
      "border-b border-border transition-colors",
      "[[data-hoverable=true]_&]:hover:bg-muted/50",
      selected && "bg-primary/5",
      className,
    )}
    {...props}
  />
));
TableRow.displayName = "TableRow";

const TableHead = React.forwardRef(
  ({ className, sortable, sorted, sortDirection, ...props }, ref) => (
    <th
      ref={ref}
      className={cn(
        "h-9 px-3 text-left align-middle text-xs font-medium text-muted-foreground uppercase tracking-wider",
        "[[data-dense=true]_&]:h-7 [[data-dense=true]_&]:px-2",
        sortable && "cursor-pointer select-none hover:text-foreground transition-colors",
        className,
      )}
      {...props}
    >
      <div className="flex items-center gap-1">
        {props.children}
        {sortable && (
          <svg
            className={cn(
              "w-3 h-3 transition-transform",
              !sorted && "opacity-0 group-hover:opacity-50",
              sorted && sortDirection === "desc" && "rotate-180",
            )}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
          </svg>
        )}
      </div>
    </th>
  ),
);
TableHead.displayName = "TableHead";

const TableCell = React.forwardRef(({ className, align = "left", ...props }, ref) => {
  const alignments = {
    left: "text-left",
    center: "text-center",
    right: "text-right",
  };

  return (
    <td
      ref={ref}
      className={cn(
        "px-3 py-2.5 align-middle",
        "[[data-dense=true]_&]:px-2 [[data-dense=true]_&]:py-1.5",
        alignments[align],
        className,
      )}
      {...props}
    />
  );
});
TableCell.displayName = "TableCell";

const TableCaption = React.forwardRef(({ className, ...props }, ref) => (
  <caption ref={ref} className={cn("mt-3 text-xs text-muted-foreground", className)} {...props} />
));
TableCaption.displayName = "TableCaption";

/**
 * TablePagination - Pagination controls for tables
 */
const TablePagination = React.forwardRef(
  (
    {
      className,
      page = 1,
      pageSize = 10,
      totalItems = 0,
      onPageChange,
      onPageSizeChange,
      pageSizeOptions = [10, 25, 50, 100],
      ...props
    },
    ref,
  ) => {
    const totalPages = Math.ceil(totalItems / pageSize);
    const startItem = (page - 1) * pageSize + 1;
    const endItem = Math.min(page * pageSize, totalItems);

    return (
      <div
        ref={ref}
        className={cn(
          "flex items-center justify-between px-3 py-2 border-t border-border text-xs",
          className,
        )}
        {...props}
      >
        <div className="flex items-center gap-2 text-muted-foreground">
          <span>Rows per page:</span>
          <select
            value={pageSize}
            onChange={(e) => onPageSizeChange?.(Number(e.target.value))}
            className="h-7 px-2 bg-transparent border border-border rounded text-foreground cursor-pointer"
          >
            {pageSizeOptions.map((size) => (
              <option key={size} value={size}>
                {size}
              </option>
            ))}
          </select>
        </div>

        <div className="flex items-center gap-4">
          <span className="text-muted-foreground">
            {startItem}-{endItem} of {totalItems}
          </span>

          <div className="flex items-center gap-1">
            <button
              onClick={() => onPageChange?.(1)}
              disabled={page === 1}
              className="p-1 rounded hover:bg-muted disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M11 19l-7-7 7-7m8 14l-7-7 7-7"
                />
              </svg>
            </button>
            <button
              onClick={() => onPageChange?.(page - 1)}
              disabled={page === 1}
              className="p-1 rounded hover:bg-muted disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M15 19l-7-7 7 7"
                />
              </svg>
            </button>
            <button
              onClick={() => onPageChange?.(page + 1)}
              disabled={page === totalPages}
              className="p-1 rounded hover:bg-muted disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 5l7 7-7 7"
                />
              </svg>
            </button>
            <button
              onClick={() => onPageChange?.(totalPages)}
              disabled={page === totalPages}
              className="p-1 rounded hover:bg-muted disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M13 5l7 7-7 7M5 5l7 7-7 7"
                />
              </svg>
            </button>
          </div>
        </div>
      </div>
    );
  },
);
TablePagination.displayName = "TablePagination";

export {
  Table,
  TableHeader,
  TableBody,
  TableFooter,
  TableHead,
  TableRow,
  TableCell,
  TableCaption,
  TablePagination,
};
