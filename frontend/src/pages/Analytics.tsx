import { useState } from 'react'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell,
  BarChart, Bar, LabelList,
} from 'recharts'
import { useAnalytics } from '../hooks/useAnalytics'
import { StatCard } from '../components/StatCard'
import { Spinner } from '../components/ui/Spinner'

const PERIODS = [7, 30, 90]

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

      {/* Key metrics + consistency ring */}
      <div className="card">
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
          Стабильность — показывает, насколько равномерно выполняются задачи каждый день (0 = хаотично, 100 = идеально стабильно).
        </p>
      </div>

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
    </div>
  )
}
