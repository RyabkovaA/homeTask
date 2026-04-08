import { useMemo } from 'react'
import { format } from 'date-fns'
import { ru } from 'date-fns/locale'
import { Clock3, CalendarRange } from 'lucide-react'
import { useTasks } from '../hooks/useTasks'
import { useEvents, useCreateEvent } from '../hooks/useEvents'
import { useAnalytics } from '../hooks/useAnalytics'
import { useAdvice } from '../hooks/useAdvice'
import { useRooms } from '../hooks/useRooms'
import { useAuthStore } from '../store/authStore'
import { TaskCard } from '../components/TaskCard'
import { ProgressBar } from '../components/ui/ProgressBar'
import { Spinner } from '../components/ui/Spinner'
import type { EventStatus, Task } from '../types'
import toast from 'react-hot-toast'
import {
  getOccurrences,
  getDueTaskEntries,
  getOccurrenceStatusMap,
} from '../utils/recurrence'
import { Badge } from '../components/ui/Badge'

function getGreeting(): string {
  const h = new Date().getHours()
  if (h < 12) return 'Доброе утро'
  if (h < 18) return 'Добрый день'
  return 'Добрый вечер'
}

function addDays(dateStr: string, days: number) {
  const d = new Date(dateStr + 'T00:00:00')
  d.setDate(d.getDate() + days)
  return d.toISOString().slice(0, 10)
}

function getNextOccurrence(task: Task, fromDate: string, horizonDays = 30) {
  const toDate = addDays(fromDate, horizonDays)
  const occurrences = getOccurrences(task, fromDate, toDate)
  return occurrences[0] ?? null
}

export default function Dashboard() {
  const { userName } = useAuthStore()
  const today = new Date().toISOString().slice(0, 10)
  const yesterday = addDays(today, -1)
  const tomorrow = addDays(today, 1)
  const monthAgo = addDays(today, -30)
  const weekAhead = addDays(today, 7)
  const monthAhead = addDays(today, 30)
  const dateLabel = format(new Date(), 'd MMMM yyyy', { locale: ru })

  const { data: tasks = [], isLoading: tasksLoading } = useTasks()
  const { data: recentEvents = [] } = useEvents({ fromDate: monthAgo, toDate: monthAhead })
  const { data: analytics } = useAnalytics(30)
  const { data: advice = [] } = useAdvice()
  const { data: rooms = [] } = useRooms()
  const createEvent = useCreateEvent()

  const todayEntries = useMemo(
    () => getDueTaskEntries(tasks, recentEvents, today),
    [tasks, recentEvents, today]
  )

  const occurrenceStatusMap = useMemo(
    () => getOccurrenceStatusMap(recentEvents),
    [recentEvents]
  )

  const roomMap = useMemo(() => new Map(rooms.map(r => [r.id, r])), [rooms])

  const doneCount = todayEntries.filter(entry =>
    occurrenceStatusMap.get(`${entry.task.id}_${today}`) === 'done'
  ).length

  const randomAdvice = useMemo(() => {
    const active = advice.filter(a => a.is_active)
    return active[Math.floor(Math.random() * active.length)] ?? null
  }, [advice])

  const nonUrgentTasks = useMemo(() => {
    const yesterdayMissed = tasks
      .filter(task => {
        const hadYesterdayOccurrence = getOccurrences(task, yesterday, yesterday).length > 0
        if (!hadYesterdayOccurrence) return false

        const status = occurrenceStatusMap.get(`${task.id}_${yesterday}`)
        return !status || status === 'skipped' || status === 'overdue'
      })
      .map(task => ({
        task,
        label: 'Со вчера',
        sublabel: 'Не завершена вчера',
        occurrenceDate: yesterday,
        priority: 1
      }))

    const skippedOrOverdueOrMoved = recentEvents
      .filter(event => event.status === 'skipped' || event.status === 'overdue' || event.status === 'moved')
      .filter(event => event.moved_to !== today)
      .map(event => {
        const task = tasks.find(t => t.id === event.task_id)
        if (!task) return null

        const label =
          event.status === 'skipped'
            ? 'Пропущена'
            : event.status === 'overdue'
              ? 'Просрочена'
              : 'Отложена'

        const sublabel =
          event.status === 'moved'
            ? `Была отложена${event.moved_to ? ` до ${format(new Date(event.moved_to), 'd MMM', { locale: ru })}` : ''}`
            : 'Можно вернуться к ней позже'

        return {
          task,
          label,
          sublabel,
          occurrenceDate: event.moved_to ?? event.occurrence_date,
          priority: 2
        }
      })
      .filter(Boolean) as Array<{
        task: Task
        label: string
        sublabel: string
        occurrenceDate: string
        priority: number
      }>

    const upcoming = tasks
      .filter(task => !todayEntries.find(entry => entry.task.id === task.id))
      .map(task => {
        const nextOccurrence = getNextOccurrence(task, tomorrow, 30)
        if (!nextOccurrence) return null

        let label = 'Позже'
        if (nextOccurrence === tomorrow) label = 'На завтра'
        else if (nextOccurrence <= weekAhead) label = 'На этой неделе'
        else if (nextOccurrence <= monthAhead) label = 'В этом месяце'

        return {
          task,
          label,
          sublabel: `Ближайшая дата: ${format(new Date(nextOccurrence), 'd MMMM', { locale: ru })}`,
          occurrenceDate: nextOccurrence,
          priority: 3
        }
      })
      .filter(Boolean) as Array<{
        task: Task
        label: string
        sublabel: string
        occurrenceDate: string
        priority: number
      }>

    const merged = [...yesterdayMissed, ...skippedOrOverdueOrMoved, ...upcoming]

    const unique = new Map<string, typeof merged[number]>()
    merged
      .sort((a, b) => a.priority - b.priority)
      .forEach(item => {
        if (!unique.has(item.task.id)) {
          unique.set(item.task.id, item)
        }
      })

    return Array.from(unique.values()).slice(0, 5)
  }, [tasks, recentEvents, occurrenceStatusMap, todayEntries, yesterday, tomorrow, weekAhead, monthAhead, today])

  const handleAction = async (
    taskId: string,
    occurrenceDate: string,
    payload: { status: EventStatus; moved_to?: string | null }
  ) => {
    try {
      await createEvent.mutateAsync({
        task_id: taskId,
        occurrence_date: occurrenceDate,
        status: payload.status,
        moved_to: payload.moved_to ?? null
      })

      toast.success(
        payload.status === 'done'
          ? '✓ Выполнено!'
          : payload.status === 'skipped'
            ? 'Пропущено'
            : payload.moved_to
              ? `Перенесено на ${format(new Date(payload.moved_to), 'd MMMM', { locale: ru })}`
              : 'Перенесено'
      )
    } catch {
      toast.error('Ошибка записи события')
    }
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <h1 className="font-display text-2xl text-forest-500">
          {getGreeting()}, {userName}!
        </h1>
        <p className="text-sm text-neutral-500 mt-0.5">{dateLabel}</p>
      </div>

      <div className="card">
        <div className="flex justify-between text-sm mb-2">
          <span className="font-medium text-neutral-700">Задачи на сегодня</span>
          <span className="text-forest-500 font-semibold">{doneCount} / {todayEntries.length}</span>
        </div>
        <ProgressBar value={doneCount} max={todayEntries.length} />
      </div>

      <div>
        <h2 className="font-display text-lg text-neutral-700 mb-3">Сегодня</h2>
        {tasksLoading ? (
          <div className="flex justify-center py-8"><Spinner className="w-8 h-8" /></div>
        ) : todayEntries.length === 0 ? (
          <div className="card text-center text-neutral-400 py-8">
            <p className="text-3xl mb-2">🎉</p>
            <p>На сегодня задач нет!</p>
          </div>
        ) : (
          <div className="space-y-3">
            {todayEntries.map(entry => (
              <TaskCard
                key={`${entry.task.id}_${entry.source}_${entry.originalOccurrenceDate ?? entry.date}`}
                task={entry.task}
                room={entry.task.room_id ? roomMap.get(entry.task.room_id) : undefined}
                occurrenceDate={entry.originalOccurrenceDate ?? entry.date}
                existingStatus={occurrenceStatusMap.get(`${entry.task.id}_${entry.date}`)}
                onAction={payload => handleAction(entry.task.id, entry.originalOccurrenceDate ?? entry.date, payload)}
                loading={createEvent.isPending}
              />
            ))}
          </div>
        )}
      </div>

      <div>
        <div className="flex items-center gap-2 mb-3">
          <Clock3 size={18} className="text-neutral-500" />
          <h2 className="font-display text-lg text-neutral-700">Можно сделать</h2>
        </div>

        {tasksLoading ? (
          <div className="flex justify-center py-6"><Spinner className="w-8 h-8" /></div>
        ) : nonUrgentTasks.length === 0 ? (
          <div className="card text-center text-neutral-400 py-8">
            <p className="text-3xl mb-2">🌿</p>
            <p>Сейчас нет дополнительных задач, о которых стоит напомнить</p>
          </div>
        ) : (
          <div className="space-y-3">
            {nonUrgentTasks.map(({ task, label, sublabel, occurrenceDate }) => (
              <div key={`${task.id}_${label}_${occurrenceDate}`} className="card">
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <p className="font-medium text-sm text-neutral-800">{task.title}</p>

                    <div className="flex items-center gap-2 mt-1 flex-wrap">
                      <Badge variant="default">{label}</Badge>
                      {task.room_id && roomMap.get(task.room_id) && (
                        <span className="text-xs text-neutral-500">
                          {roomMap.get(task.room_id)?.icon} {roomMap.get(task.room_id)?.name}
                        </span>
                      )}
                    </div>

                    <p className="text-xs text-neutral-500 mt-2">{sublabel}</p>
                  </div>

                  <div className="text-right text-xs text-neutral-400 flex-shrink-0">
                    <div className="flex items-center gap-1 justify-end">
                      <CalendarRange size={13} />
                      {format(new Date(occurrenceDate), 'd MMM', { locale: ru })}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

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