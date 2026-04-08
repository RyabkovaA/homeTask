import { useMemo } from 'react'
import { format } from 'date-fns'
import { ru } from 'date-fns/locale'
import { useTasks } from '../hooks/useTasks'
import { useEvents, useCreateEvent } from '../hooks/useEvents'
import { useAnalytics } from '../hooks/useAnalytics'
import { useAdvice } from '../hooks/useAdvice'
import { useRooms } from '../hooks/useRooms'
import { useAuthStore } from '../store/authStore'
import { isDueToday } from '../utils/recurrence'
import { TaskCard } from '../components/TaskCard'
import { ProgressBar } from '../components/ui/ProgressBar'
import { Spinner } from '../components/ui/Spinner'
import type { EventStatus } from '../types'
import toast from 'react-hot-toast'

function getGreeting(): string {
  const h = new Date().getHours()
  if (h < 12) return 'Доброе утро'
  if (h < 18) return 'Добрый день'
  return 'Добрый вечер'
}

export default function Dashboard() {
  const { userName } = useAuthStore()
  const today = new Date().toISOString().slice(0, 10)
  const dateLabel = format(new Date(), 'd MMMM yyyy', { locale: ru })

  const { data: tasks = [], isLoading: tasksLoading } = useTasks()
  const { data: events = [] } = useEvents({ fromDate: today, toDate: today }) 
  const { data: analytics } = useAnalytics(30)
  const { data: advice = [] } = useAdvice()
  const { data: rooms = [] } = useRooms()
  const createEvent = useCreateEvent()

  const todayTasks = useMemo(() => tasks.filter(t => isDueToday(t)), [tasks])

  const eventMap = useMemo(() => {
    const m = new Map<string, EventStatus>()
    events.forEach(e => m.set(e.task_id, e.status))
    return m
  }, [events])

  const doneCount = todayTasks.filter(t => eventMap.get(t.id) === 'done').length
  const roomMap = useMemo(() => new Map(rooms.map(r => [r.id, r])), [rooms])

  const randomAdvice = useMemo(() => {
    const active = advice.filter(a => a.is_active)
    return active[Math.floor(Math.random() * active.length)] ?? null
  }, [advice])

  const handleAction = async (taskId: string, status: EventStatus) => {
    try {
      await createEvent.mutateAsync({ task_id: taskId, occurrence_date: today, status })
      toast.success(status === 'done' ? '✓ Выполнено!' : status === 'skipped' ? 'Пропущено' : 'Перенесено')
    } catch {
      toast.error('Ошибка записи события')
    }
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="font-display text-2xl text-forest-500">
          {getGreeting()}, {userName}!
        </h1>
        <p className="text-sm text-neutral-500 mt-0.5">{dateLabel}</p>
      </div>

      {/* Day progress */}
      <div className="card">
        <div className="flex justify-between text-sm mb-2">
          <span className="font-medium text-neutral-700">Задачи на сегодня</span>
          <span className="text-forest-500 font-semibold">{doneCount} / {todayTasks.length}</span>
        </div>
        <ProgressBar value={doneCount} max={todayTasks.length} />
      </div>

      {/* Today's tasks */}
      <div>
        <h2 className="font-display text-lg text-neutral-700 mb-3">Сегодня</h2>
        {tasksLoading ? (
          <div className="flex justify-center py-8"><Spinner className="w-8 h-8" /></div>
        ) : todayTasks.length === 0 ? (
          <div className="card text-center text-neutral-400 py-8">
            <p className="text-3xl mb-2">🎉</p>
            <p>На сегодня задач нет!</p>
          </div>
        ) : (
          <div className="space-y-3">
            {todayTasks.map(task => (
              <TaskCard
                key={task.id}
                task={task}
                room={task.room_id ? roomMap.get(task.room_id) : undefined}
                occurrenceDate={today}
                existingStatus={eventMap.get(task.id)}
                onAction={status => handleAction(task.id, status)}
                loading={createEvent.isPending}
              />
            ))}
          </div>
        )}
      </div>

      {/* Metrics */}
      {analytics && (
        <div className="grid grid-cols-2 gap-3">
          <div className="card text-center">
            <p className="text-3xl font-display text-forest-500">{analytics.metrics.streak}</p>
            <p className="text-xs text-neutral-500 mt-1">Серия дней 🔥</p>
          </div>
          <div className="card text-center">
            <p className="text-3xl font-display text-forest-500">{analytics.metrics.adherence_rate}%</p>
            <p className="text-xs text-neutral-500 mt-1">Соблюдение</p>
          </div>
        </div>
      )}

      {/* Advice of the day */}
      {randomAdvice && (
        <div className="card bg-forest-50 border-forest-200">
          <p className="text-xs font-medium text-forest-500 uppercase tracking-wide mb-1">Совет дня</p>
          <h3 className="font-display text-base text-forest-600 mb-1">{randomAdvice.title}</h3>
          <p className="text-sm text-neutral-600">{randomAdvice.content}</p>
        </div>
      )}
    </div>
  )
}
