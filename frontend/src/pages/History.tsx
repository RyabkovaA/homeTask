import { useMemo, useState } from 'react'
import { History as HistoryIcon, Filter, CalendarDays } from 'lucide-react'
import { useEvents } from '../hooks/useEvents'
import { useRooms } from '../hooks/useRooms'
import { Badge } from '../components/ui/Badge'
import { Spinner } from '../components/ui/Spinner'
import type { EventStatus } from '../types'

const STATUS_LABELS: Record<EventStatus, string> = {
  done: 'Выполнено',
  skipped: 'Пропущено',
  overdue: 'Просрочено',
  moved: 'Перенесено'
}

const STATUS_VARIANTS: Record<EventStatus, 'success' | 'warning' | 'danger' | 'info'> = {
  done: 'success',
  skipped: 'warning',
  overdue: 'danger',
  moved: 'info'
}

function formatDate(value: string | null) {
  if (!value) return ''
  return new Date(value).toLocaleDateString('ru-RU')
}

function formatDateTime(value: string) {
  return new Date(value).toLocaleString('ru-RU')
}

export default function History() {
  const today = new Date()
  const monthAgo = new Date()
  monthAgo.setDate(today.getDate() - 30)

  const [statusFilter, setStatusFilter] = useState<EventStatus | ''>('')
  const [roomFilter, setRoomFilter] = useState('')
  const [fromDate, setFromDate] = useState(monthAgo.toISOString().slice(0, 10))
  const [toDate, setToDate] = useState(today.toISOString().slice(0, 10))

  const { data: rooms = [] } = useRooms()
  const { data: events = [], isLoading } = useEvents({
    fromDate,
    toDate,
    status: statusFilter,
    roomId: roomFilter || undefined
  })

  const groupedEvents = useMemo(() => {
    const groups = new Map<string, typeof events>()

    events.forEach(event => {
      const key = event.occurrence_date
      if (!groups.has(key)) groups.set(key, [])
      groups.get(key)!.push(event)
    })

    return Array.from(groups.entries())
  }, [events])

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div className="flex items-center gap-3">
        <div className="w-11 h-11 rounded-2xl bg-forest-100 flex items-center justify-center text-forest-500">
          <HistoryIcon size={22} />
        </div>
        <div>
          <h1 className="font-display text-2xl text-forest-500">История задач</h1>
          <p className="text-sm text-neutral-500">
            Журнал выполненных, пропущенных, перенесённых и просроченных задач
          </p>
        </div>
      </div>

      <div className="card space-y-4">
        <div className="flex items-center gap-2 text-neutral-700">
          <Filter size={16} />
          <p className="text-sm font-medium">Фильтры</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
          <select
            className="input"
            value={statusFilter}
            onChange={e => setStatusFilter(e.target.value as EventStatus | '')}
          >
            <option value="">Все статусы</option>
            <option value="done">Выполнено</option>
            <option value="skipped">Пропущено</option>
            <option value="moved">Перенесено</option>
            <option value="overdue">Просрочено</option>
          </select>

          <select
            className="input"
            value={roomFilter}
            onChange={e => setRoomFilter(e.target.value)}
          >
            <option value="">Все комнаты</option>
            {rooms.map(room => (
              <option key={room.id} value={room.id}>
                {room.icon} {room.name}
              </option>
            ))}
          </select>

          <div>
            <label className="label">От</label>
            <input
              type="date"
              className="input"
              value={fromDate}
              onChange={e => setFromDate(e.target.value)}
            />
          </div>

          <div>
            <label className="label">До</label>
            <input
              type="date"
              className="input"
              value={toDate}
              onChange={e => setToDate(e.target.value)}
            />
          </div>
        </div>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-12">
          <Spinner className="w-8 h-8" />
        </div>
      ) : groupedEvents.length === 0 ? (
        <div className="card text-center text-neutral-400 py-10">
          <p className="text-3xl mb-2">🕘</p>
          <p>История по выбранным фильтрам пуста</p>
        </div>
      ) : (
        <div className="space-y-6">
          {groupedEvents.map(([date, items]) => (
            <section key={date} className="space-y-3">
              <div className="flex items-center gap-2 text-neutral-600">
                <CalendarDays size={16} />
                <h2 className="font-display text-lg">{formatDate(date)}</h2>
              </div>

              <div className="space-y-3">
                {items.map(item => (
                  <div key={item.id} className="card">
                    <div className="flex items-start justify-between gap-3 mb-3">
                      <div className="min-w-0">
                        <h3 className="font-medium text-neutral-800">
                          {item.task_title}
                        </h3>

                        <div className="flex flex-wrap items-center gap-2 mt-1 text-xs text-neutral-500">
                          {item.room_name && (
                            <span>
                              {item.room_icon ?? '🏠'} {item.room_name}
                            </span>
                          )}
                          <span>•</span>
                          <span>Автор: {item.actor_name}</span>
                        </div>
                      </div>

                      <Badge variant={STATUS_VARIANTS[item.status]}>
                        {STATUS_LABELS[item.status]}
                      </Badge>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm text-neutral-600">
                      <div>
                        <span className="text-neutral-400">Плановая дата: </span>
                        <span>{formatDate(item.occurrence_date)}</span>
                      </div>

                      <div>
                        <span className="text-neutral-400">Зафиксировано: </span>
                        <span>{formatDateTime(item.created_at)}</span>
                      </div>

                      {item.status === 'moved' && item.moved_to && (
                        <div>
                          <span className="text-neutral-400">Перенесено на: </span>
                          <span>{formatDate(item.moved_to)}</span>
                        </div>
                      )}
                    </div>

                    {item.note && (
                      <div className="mt-3 pt-3 border-t border-beige-200">
                        <p className="text-xs font-medium text-neutral-500 uppercase tracking-wide mb-1">
                          Комментарий
                        </p>
                        <p className="text-sm text-neutral-700">{item.note}</p>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </section>
          ))}
        </div>
      )}
    </div>
  )
}