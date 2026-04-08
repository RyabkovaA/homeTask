import { ButtonHTMLAttributes } from 'react'
import clsx from 'clsx'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger'
  size?: 'sm' | 'md' | 'lg'
}

export function Button({ variant = 'primary', size = 'md', className, children, ...props }: ButtonProps) {
  return (
    <button
      className={clsx(
        'font-body font-medium rounded-xl transition-all duration-200 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed',
        {
          'bg-forest-400 hover:bg-forest-500 text-white shadow-sm hover:shadow-md': variant === 'primary',
          'bg-beige-200 hover:bg-beige-300 text-forest-500': variant === 'secondary',
          'text-forest-400 hover:bg-forest-50': variant === 'ghost',
          'bg-red-500 hover:bg-red-600 text-white': variant === 'danger',
          'px-3 py-1.5 text-sm': size === 'sm',
          'px-5 py-2.5 text-sm': size === 'md',
          'px-6 py-3 text-base': size === 'lg',
        },
        className
      )}
      {...props}
    >
      {children}
    </button>
  )
}
