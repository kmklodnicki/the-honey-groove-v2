import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva } from "class-variance-authority";

import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-full text-sm font-medium transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#D4A828] focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0",
  {
    variants: {
      variant: {
        /* Gold Primary — Foiled Gold bg, white text */
        default:
          "bg-[#D4A828] text-white shadow-[0_2px_4px_#D4A82828,0_4px_12px_#D4A82820] hover:bg-[#E8CA5A] hover:shadow-[0_2px_8px_#D4A82840]",
        /* Gold CTA Foil — same + inner shine */
        gold:
          "bg-[#D4A828] text-white shadow-[0_2px_4px_#D4A82828,0_4px_12px_#D4A82820,inset_0_1px_0_rgba(255,255,255,0.2)] hover:bg-[#E8CA5A]",
        /* Merlot destructive */
        destructive:
          "bg-[#9B2C2C] text-white shadow-sm hover:bg-[#7a2222]",
        /* Navy Secondary — outline, gold hover fill */
        outline:
          "border border-[#1E2A3A] text-[#1E2A3A] bg-transparent shadow-sm hover:bg-[#D4A828] hover:text-white hover:border-[#D4A828]",
        /* Navy Accent — deep ink bg, white text */
        secondary:
          "bg-[#1E2A3A] text-white shadow-[0_2px_4px_#1E2A3A20,0_4px_12px_#1E2A3A12] hover:bg-[#2A3B50]",
        ghost: "text-[#1E2A3A] hover:bg-[#F0E6C8] hover:text-[#1E2A3A]",
        link: "text-[#D4A828] underline-offset-4 hover:underline hover:text-[#E8CA5A]",
      },
      size: {
        default: "h-9 px-4 py-2",
        sm: "h-8 rounded-md px-3 text-xs",
        lg: "h-10 rounded-md px-8",
        icon: "h-9 w-9",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

const Button = React.forwardRef(({ className, variant, size, asChild = false, ...props }, ref) => {
  const Comp = asChild ? Slot : "button"
  return (
    <Comp
      className={cn(buttonVariants({ variant, size, className }))}
      ref={ref}
      {...props} />
  );
})
Button.displayName = "Button"

export { Button, buttonVariants }
