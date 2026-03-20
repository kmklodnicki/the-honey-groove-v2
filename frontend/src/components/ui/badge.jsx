import * as React from "react"
import { cva } from "class-variance-authority";

import { cn } from "@/lib/utils"

const badgeVariants = cva(
  "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-[#D4A828] focus:ring-offset-2",
  {
    variants: {
      variant: {
        /* Gold Badge */
        default:
          "border-transparent bg-[#D4A828] text-white shadow-[0_2px_6px_#D4A82830] hover:bg-[#E8CA5A]",
        /* Navy Badge */
        secondary:
          "border-transparent bg-[#1E2A3A] text-white shadow-[0_2px_6px_#1E2A3A25] hover:bg-[#2A3B50]",
        /* Merlot Badge */
        destructive:
          "border-transparent bg-[#9B2C2C] text-white shadow-sm hover:bg-[#7a2222]",
        /* Gold Wash outline pill */
        outline: "border-[#D4A828] text-[#1E2A3A] bg-[#F0E6C8]",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

function Badge({
  className,
  variant,
  ...props
}) {
  return (<div className={cn(badgeVariants({ variant }), className)} {...props} />);
}

export { Badge, badgeVariants }
