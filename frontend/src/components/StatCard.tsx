interface StatCardProps {
  label: string
  value: string | number
  unit?: string
  icon?: string
  trend?: number
}

export function StatCard({ label, value, unit, icon, trend }: StatCardProps) {
  return (
    <div className="card">
      <div className="flex items-start justify-between">
        <div>
          <p className="label">{label}</p>
          <p className="text-3xl font-display text-forest-500 mt-1">
            {value}
            {unit && <span className="text-base text-neutral-500 ml-1">{unit}</span>}
          </p>
        </div>
        {icon && <span className="text-xl sm:text-3xl flex-shrink-0">{icon}</span>}
      </div>
      {trend !== undefined && (
        <p className={`text-xs mt-2 ${trend >= 0 ? 'text-forest-400' : 'text-red-500'}`}>
          {trend >= 0 ? '↑' : '↓'} {Math.abs(trend)}% vs прошлый период
        </p>
      )}
    </div>
  )
}
