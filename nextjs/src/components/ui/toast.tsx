import * as React from "react"
import { type VariantProps } from "class-variance-authority"
import { X } from "lucide-react"

import { cn } from "@/lib/utils"

export type ToastProps = React.HTMLAttributes<HTMLDivElement> & {
  variant?: "default" | "destructive"
}

export type ToastActionElement = React.ReactElement

const Toast = React.forwardRef<
  HTMLDivElement,
  ToastProps
>(({ className, variant, ...props }, ref) => {
  return (
    <div
      ref={ref}
      className={cn(
        "group pointer-events-auto relative flex w-full items-center justify-between space-x-2 overflow-hidden rounded-md border p-4 pr-6 shadow-lg transition-all",
        variant === "destructive" && "destructive group border-destructive bg-destructive text-destructive-foreground",
        className
      )}
      {...props}
    />
  )
})
Toast.displayName = "Toast"

export { Toast }
