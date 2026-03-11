import { cn } from "@/lib/utils"

function Skeleton({
  className,
  ...props
}) {
  return (
    <div
      className={cn("honey-shimmer rounded-md", className)}
      {...props} />
  );
}

export { Skeleton }
