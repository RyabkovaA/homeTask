import { HTMLAttributes } from 'react'
import clsx from 'clsx'

export function Card({ className, children, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={clsx('bg-beige-50 rounded-xl3 shadow-card border border-beige-200 p-5', className)}
      {...props}
    >
      {children}
    </div>
  )
}
