export function Spinner({ className = '' }: { className?: string }) {
  return (
    <div className={`animate-spin rounded-full border-2 border-beige-300 border-t-forest-400 ${className}`} />
  )
}
