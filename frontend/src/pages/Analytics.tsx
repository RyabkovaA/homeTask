import { useState } from 'react'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell,
  BarChart, Bar, LabelList,
} from 'recharts'
import { AlertTriangle, Info, CheckCircle, ChevronDown, ChevronUp, BarChart2 } from 'lucide-react'
import { useAnalytics } from '../hooks/useAnalytics'
import { useHabitInsights } from '../hooks/useRag'
import { StatCard } from '../components/StatCard'
import { AdvicePanel } from '../components/AdvicePanel'
import { Spinner } from '../components/ui/Spinner'
import type { HabitInsight, InsightSeverity } from '../types'

const PERIODS = [7, 30, 90]

// ---------------------------------------------------------------------------
// ConsistencyRing
// ---------------------------------------------------------------------------
function ConsistencyRing({ score }: { score: number }) {
  const r = 32
  const circ = 2 * Math.PI * r
  const filled = (score / 100) * circ
  const color = score >= 70 ? '#4A7C59' : score >= 40 ? '#F59E0B' : '#EF4444'

  return (
    <div className="flex flex-col items-center gap-1">
      <svg width={80} height={80} viewBox="0 0 80 80">
        <circle cx={40} cy={40} r={r} fill="none" stroke="#EDE5D5" strokeWidth={8} />
        <circle
          cx={40} cy={40} r={r} fill="none"
          stroke={color} strokeWidth={8}
          strokeDasharray={`${filled} ${circ}`}
          strokeLinecap="round"
          transform="rotate(-90 40 40)"
        />
        <text x={40} y={45} textAnchor="middle" fontSize={14} fontWeight={600} fill={color}>
          {score}
        </text>
      </svg>
      <p className="text-xs text-neutral-500">Стабильность</p>
    </div>
  )
}

// ---------------------------------------------------------------------------
// InsightCard
// ---------------------------------------------------------------------------
const SEVERITY_CONFIG: Record<InsightSeverity, {
  icon: React.ElementType
  bg: string
  border: string
  iconColor: string
  label: string
}> = {
  critical: {
    icon: AlertTriangle,
    bg: 'bg-red-50',
    border: 'border-red-200',
    iconColor: 'text-red-500',
    label: 'Критично',
  },
  warning: {
    icon: AlertTriangle,
    bg: 'bg-amber-50',
    border: 'border-amber-200',
    iconColor: 'text-amber-500',
    label: 'Внимание',
  },
  info: {
    icon: Info,
    bg: 'bg-forest-50',
    border: 'border-forest-200',
    iconColor: 'text-forest-500',
    label: 'Инфо',
  },
}

function InsightCard({ insight }: { insight: HabitInsight }) {
  const [expanded, setExpanded] = useState(false)
  const cfg = SEVERITY_CONFIG[insight.severity]
  const Icon = cfg.icon

  return (
    <div className={`rounded-xl border ${cfg.border} ${cfg.bg} p-3 space-y-2`}>
      <div className="flex items-start gap-2">
        <Icon size={16} className={`${cfg.iconColor} flex-shrink-0 mt-0.5`} />
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold text-neutral-800">{insight.title}</p>
          <p className="text-xs text-neutral-600 mt-0.5 leading-relaxed">{insight.description}</p>
        </div>

        {insight.advice && (
          <button
            onClick={() => setExpanded(e => !e)}
            className="flex-shrink-0 text-xs text-forest-600 font-medium flex items-center gap-0.5 hover:text-forest-700 transition-colors"
          >
            Совет
            {expanded ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
          </button>
        )}
      </div>

      {expanded && insight.advice && (
        <AdvicePanel advice={insight.advice} compact />
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// HabitInsightsSection
// ---------------------------------------------------------------------------
function HabitInsightsSection({ days }: { days: number }) {
  const { data: insights, isLoading } = useHabitInsights(days)

  if (isLoading) {
    return (
      <div className="card flex items-center gap-2 py-4 text-sm text-neutral-500">
        <Spinner className="w-4 h-4" />
        Анализируем поведение пользователей...
      </div>
    )
  }
  if (!insights) return null

  const statusColors = {
    good: 'text-forest-600 bg-forest-50 border-forest-200',
    attention: 'text-amber-700 bg-amber-50 border-amber-200',
    critical: 'text-red-700 bg-red-50 border-red-200',
  }
  const StatusIcon = insights.overall_status === 'good' ? CheckCircle : AlertTriangle

  return (
    <div className="card space-y-4">
      <div className="flex items-start gap-3">
        <div className="flex-1">
          <h2 className="font-display text-base text-neutral-700 mb-1">Анализ привычек</h2>
          <div className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg border text-xs font-medium ${statusColors[insights.overall_status]}`}>
            <StatusIcon size={13} />
            {insights.adherence_summary}
          </div>
        </div>
      </div>

      {insights.insights.length === 0 ? (
        <div className="flex items-center gap-2 text-sm text-neutral-500 py-2">
          <CheckCircle size={16} className="text-forest-500" />
          Проблемных паттернов не обнаружено. Отличная работа!
        </div>
      ) : (
        <div className="space-y-2">
          {insights.insights.map((insight, i) => (
            <InsightCard key={i} insight={insight} />
          ))}
        </div>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Main Analytics page
// ---------------------------------------------------------------------------
export default function Analytics() {
  const [days, setDays] = useState(30)
  const { data, isLoading } = useAnalytics(days)

  if (isLoading) {
    return (
      <div className="flex justify-center py-20">
        <Spinner className="w-10 h-10" />
      </div>
    )
  }

  if (!data) return null

  const { metrics, daily_trend, load_distribution, room_stats } = data
  const hasData = metrics.total_planned > 0

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <h1 className="font-display text-2xl text-forest-500">Аналитика</h1>
        <div className="flex gap-1">
          {PERIODS.map(p => (
            <button
              key={p}
              onClick={() => setDays(p)}
              className={`px-4 py-1.5 rounded-full text-sm font-medium transition-all ${
                days === p ? 'bg-forest-400 text-white' : 'bg-beige-200 text-neutral-600 hover:bg-beige-300'
              }`}
            >
              {p} дней
            </button>
          ))}
        </div>
      </div>

      {!hasData && (
        <div className="card flex flex-col items-center gap-3 py-10 text-center">
          <BarChart2 size={40} className="text-beige-400" />
          <p className="font-display text-lg text-neutral-600">Пока недостаточно данных</p>
          <p className="text-sm text-neutral-400 max-w-xs">
            Создайте задачи и отмечайте их выполнение — аналитика появится за выбранный период.
          </p>
        </div>
      )}

      {hasData && <><div className="card">
        <div className="flex flex-wrap gap-4 items-center justify-between">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 flex-1">
            <StatCard label="Соблюдение" value={metrics.adherence_rate} unit="%" icon="📊" />
            <StatCard label="Серия" value={metrics.streak} unit="дн" icon="🔥" />
            <StatCard label="Выполнено" value={metrics.completion_ratio} unit="%" icon="✅" />
            <StatCard label="Просрочено" value={metrics.overdue_rate} unit="%" icon="⚠️" />
          </div>
          <ConsistencyRing score={metrics.consistency_score} />
        </div>
        <p className="text-xs text-neutral-400 mt-3">
          Стабильность — насколько равномерно выполняются задачи каждый день (0 = хаотично, 100 = идеально стабильно).
        </p>
      </div>

      {/* Habit insights — AI section */}
      <HabitInsightsSection days={days} />

      {/* Daily trend */}
      <div className="card">
        <h2 className="font-display text-base text-neutral-700 mb-4">Тренд выполнения</h2>
        <ResponsiveContainer width="100%" height={220}>
          <LineChart data={daily_trend} margin={{ top: 5, right: 5, bottom: 5, left: -20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#EDE5D5" />
            <XAxis
              dataKey="date"
              tick={{ fontSize: 10, fill: '#9CA3AF' }}
              tickFormatter={v => v.slice(5)}
              interval={Math.max(0, Math.floor(daily_trend.length / 6))}
            />
            <YAxis tick={{ fontSize: 10, fill: '#9CA3AF' }} domain={[0, 100]} />
            <Tooltip
              formatter={(v: number) => [`${v}%`, 'Выполнение']}
              labelFormatter={l => `Дата: ${l}`}
              contentStyle={{
                background: '#FDFAF4',
                border: '1px solid #EDE5D5',
                borderRadius: 12,
                fontSize: 12,
              }}
            />
            <Line
              type="monotone"
              dataKey="rate"
              stroke="#4A7C59"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4, fill: '#4A7C59' }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Room breakdown */}
      {room_stats.length > 0 && (
        <div className="card">
          <h2 className="font-display text-base text-neutral-700 mb-4">Соблюдение по комнатам</h2>
          <ResponsiveContainer width="100%" height={Math.max(180, room_stats.length * 44)}>
            <BarChart
              data={room_stats}
              layout="vertical"
              margin={{ top: 0, right: 48, bottom: 0, left: 8 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#EDE5D5" horizontal={false} />
              <XAxis
                type="number"
                domain={[0, 100]}
                tick={{ fontSize: 10, fill: '#9CA3AF' }}
                tickFormatter={v => `${v}%`}
              />
              <YAxis
                type="category"
                dataKey="room_name"
                tick={{ fontSize: 12, fill: '#374151' }}
                width={110}
                tickFormatter={(v, i) => `${room_stats[i]?.room_icon ?? ''} ${v}`}
              />
              <Tooltip
                formatter={(v: number, _, props) => [
                  `${v}% (${props.payload.total_done}/${props.payload.total_planned})`,
                  'Выполнено',
                ]}
                contentStyle={{
                  background: '#FDFAF4',
                  border: '1px solid #EDE5D5',
                  borderRadius: 12,
                  fontSize: 12,
                }}
              />
              <Bar dataKey="adherence_rate" radius={[0, 6, 6, 0]} fill="#4A7C59">
                <LabelList
                  dataKey="adherence_rate"
                  position="right"
                  formatter={(v: number) => `${v}%`}
                  style={{ fontSize: 11, fill: '#6B7280' }}
                />
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Load distribution */}
      {load_distribution.length > 0 && (
        <div className="card overflow-visible">
          <h2 className="font-display text-base text-neutral-700 mb-4">Нагрузка по участникам</h2>

          <div className="grid grid-cols-1 lg:grid-cols-[minmax(320px,1fr)_220px] gap-6 items-center">
            <div className="h-[260px] min-w-0">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart margin={{ top: 10, right: 10, bottom: 10, left: 10 }}>
                  <Pie
                    data={load_distribution}
                    dataKey="done_count"
                    nameKey="member_name"
                    cx="50%"
                    cy="50%"
                    innerRadius={42}
                    outerRadius={78}
                    paddingAngle={2}
                    stroke="#FDFAF4"
                    strokeWidth={2}
                    labelLine={false}
                  >
                    {load_distribution.map((item, idx) => (
                      <Cell key={idx} fill={item.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    formatter={(v: number, _n, props) => [`${v}`, props.payload.member_name]}
                    contentStyle={{
                      background: '#FDFAF4',
                      border: '1px solid #EDE5D5',
                      borderRadius: 12,
                      fontSize: 12,
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>

            <div className="space-y-2 min-w-0">
              {load_distribution.map(item => (
                <div
                  key={item.member_id}
                  className="flex items-center gap-2 rounded-xl border border-beige-200 bg-beige-50 px-3 py-2"
                >
                  <div
                    className="w-3 h-3 rounded-full flex-shrink-0"
                    style={{ background: item.color }}
                  />
                  <div className="min-w-0 flex-1">
                    <p className="text-sm text-neutral-700 truncate">{item.member_name}</p>
                    <p className="text-xs text-neutral-400">{item.percentage}% нагрузки</p>
                  </div>
                  <span className="text-sm font-semibold text-forest-500">{item.done_count}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Period totals */}
      <div className="card">
        <h2 className="font-display text-base text-neutral-700 mb-3">Итого за период</h2>
        <div className="grid grid-cols-3 gap-4 text-center">
          <div>
            <p className="text-2xl font-display text-forest-500">{metrics.total_planned}</p>
            <p className="text-xs text-neutral-500 mt-0.5">Запланировано</p>
          </div>
          <div>
            <p className="text-2xl font-display text-forest-500">{metrics.total_done}</p>
            <p className="text-xs text-neutral-500 mt-0.5">Выполнено</p>
          </div>
          <div>
            <p className="text-2xl font-display text-red-500">{metrics.total_overdue}</p>
            <p className="text-xs text-neutral-500 mt-0.5">Просрочено</p>
          </div>
        </div>
      </div>
      </>}
    </div>
  )
}
