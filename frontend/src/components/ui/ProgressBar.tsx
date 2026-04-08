interface ProgressBarProps {
  value: number
  max?: number
  className?: string
  color?: string
}

export function ProgressBar({ value, max = 100, className = '', color = 'bg-forest-400' }: ProgressBarProps) {
  const pct = Math.min(100, Math.round((value / Math.max(max, 1)) * 100))
  return (
    <div className={`h-2 bg-beige-200 rounded-full overflow-hidden ${className}`}>
      <div
        className={`h-full rounded-full transition-all duration-500 ${color}`}
        style={{ width: `${pct}%` }}
      />
    </div>
  )
}
