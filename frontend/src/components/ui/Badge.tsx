import { HTMLAttributes } from 'react'
import clsx from 'clsx'

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: 'default' | 'success' | 'warning' | 'danger' | 'info'
}

const variantClasses = {
  default: 'bg-beige-200 text-neutral-600',
  success: 'bg-forest-100 text-forest-600',
  warning: 'bg-amber-100 text-amber-700',
  danger: 'bg-red-100 text-red-700',
  info: 'bg-blue-100 text-blue-700',
}

export function Badge({ variant = 'default', className, children, ...props }: BadgeProps) {
  return (
    <span
      className={clsx('inline-flex items-center px-2 py-0.5 rounded-lg text-xs font-medium', variantClasses[variant], className)}
      {...props}
    >
      {children}
    </span>
  )
}
