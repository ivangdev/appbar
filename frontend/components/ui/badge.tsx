import * as React from "react";
import { cn } from "@/lib/utils";

export interface BadgeProps {
  className?: string;
  variant?: string;
  style?: React.CSSProperties;
  children?: React.ReactNode;
}

const variantClasses: Record<string, string> = {
  default: "rounded text-xs font-medium px-2 py-1 border border-slate-200 bg-white text-slate-500",
  secondary: "rounded text-xs font-medium px-2 py-1 border border-slate-200 bg-white text-slate-600",
  outline: "rounded text-xs font-medium px-2 py-1 border border-slate-300 bg-transparent text-slate-600",
  danger: "rounded text-xs font-medium px-2 py-1 border border-red-200 bg-red-50 text-red-600",
  open: "rounded text-xs font-medium px-2 py-1 border border-blue-200 bg-blue-50 text-blue-700",
  closed: "rounded text-xs font-medium px-2 py-1 border border-slate-200 bg-slate-100 text-slate-600",
  partially_paid: "rounded text-xs font-medium px-2 py-1 border border-amber-200 bg-amber-50 text-amber-700",
  paid: "rounded text-xs font-medium px-2 py-1 border border-green-200 bg-green-50 text-green-700",
  cancelled: "rounded text-xs font-medium px-2 py-1 border border-red-200 bg-red-50 text-red-600",
};

const Badge = React.forwardRef<HTMLSpanElement, BadgeProps>(
  ({ className, variant = "default", children, style, ...props }, ref) => {
    return (
      <span
        ref={ref}
        className={cn(variantClasses[variant] ?? variantClasses.default, className)}
        style={style}
        {...props}
      >
        {children}
      </span>
    );
  },
);

Badge.displayName = "Badge";

export { Badge };
