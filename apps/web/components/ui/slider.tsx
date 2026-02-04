"use client"

import * as React from "react"
import { cn } from "@/lib/utils"

interface SliderProps {
  value?: number[]
  onValueChange?: (value: number[]) => void
  max?: number
  min?: number
  step?: number
  className?: string
  disabled?: boolean
}

const Slider = React.forwardRef<HTMLInputElement, SliderProps>(
  ({ className, value = [0], onValueChange, max = 100, min = 0, step = 1, disabled, ...props }, ref) => {
    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      onValueChange?.([parseInt(e.target.value, 10)])
    }

    return (
      <input
        type="range"
        ref={ref}
        value={value[0]}
        onChange={handleChange}
        min={min}
        max={max}
        step={step}
        disabled={disabled}
        className={cn(
          "w-full h-2 bg-secondary rounded-lg appearance-none cursor-pointer",
          "accent-primary",
          disabled && "opacity-50 cursor-not-allowed",
          className
        )}
        {...props}
      />
    )
  }
)
Slider.displayName = "Slider"

export { Slider }
