import type { Task, TaskHistoryItem, EventStatus } from '../types'

function addDays(date: Date, days: number): Date {
  const d = new Date(date)
  d.setDate(d.getDate() + days)
  return d
}

function addMonths(date: Date, months: number): Date {
  const d = new Date(date)
  d.setMonth(d.getMonth() + months)
  return d
}

function toDateObj(str: string): Date {
  return new Date(str + 'T00:00:00')
}

function toStr(d: Date): string {
  return d.toISOString().slice(0, 10)
}

function makeOccurrenceKey(taskId: string, date: string) {
  return `${taskId}_${date}`
}

export function getOccurrences(task: Task, fromDate: string, toDate: string): string[] {
  const from = toDateObj(fromDate)
  const to = toDateObj(toDate)
  const start = toDateObj(task.start_date)

  if (task.frequency === 'once') {
    if (start >= from && start <= to) return [task.start_date]
    return []
  }

  const dates: string[] = []

  if (task.frequency === 'monthly') {
    let c = new Date(start)
    while (c < from) {
      c = addMonths(c, 1)
    }
    while (c <= to) {
      dates.push(toStr(c))
      c = addMonths(c, 1)
    }
    return dates
  }

  let current = start > from ? new Date(start) : new Date(from)

  while (current <= to) {
    if (task.frequency === 'daily') {
      dates.push(toStr(current))
      current = addDays(current, 1)
    } else if (task.frequency === 'weekly') {
      const days = task.days_of_week ?? [start.getDay() === 0 ? 6 : start.getDay() - 1]
      const jsDow = current.getDay()
      const monDow = jsDow === 0 ? 6 : jsDow - 1
      if (days.includes(monDow)) {
        dates.push(toStr(current))
      }
      current = addDays(current, 1)
    } else if (task.frequency === 'custom') {
      dates.push(toStr(current))
      current = addDays(current, task.custom_interval_days ?? 1)
    } else {
      break
    }
  }

  return dates
}

export function isDueToday(task: Task): boolean {
  const today = new Date().toISOString().slice(0, 10)
  return getOccurrences(task, today, today).length > 0
}

export function getOccurrenceStatusMap(
  events: Array<Pick<TaskHistoryItem, 'task_id' | 'occurrence_date' | 'status'>>
) {
  const map = new Map<string, EventStatus>()

  events.forEach(event => {
    map.set(makeOccurrenceKey(event.task_id, event.occurrence_date), event.status)
  })

  return map
}

export interface DueTaskEntry {
  task: Task
  date: string
  source: 'regular' | 'moved'
  originalOccurrenceDate?: string
}

export function getDueTaskEntries(
  tasks: Task[],
  events: TaskHistoryItem[],
  targetDate: string
): DueTaskEntry[] {
  const statusMap = getOccurrenceStatusMap(events)
  const taskMap = new Map(tasks.map(task => [task.id, task]))

  const regularEntries: DueTaskEntry[] = tasks
    .filter(task => getOccurrences(task, targetDate, targetDate).length > 0)
    .filter(task => statusMap.get(makeOccurrenceKey(task.id, targetDate)) !== 'moved')
    .map(task => ({
      task,
      date: targetDate,
      source: 'regular' as const
    }))

  const movedEntries: DueTaskEntry[] = events
    .filter(event => event.status === 'moved' && event.moved_to === targetDate)
    .map(event => {
      const task = taskMap.get(event.task_id)
      if (!task) return null

      return {
        task,
        date: targetDate,
        source: 'moved' as const,
        originalOccurrenceDate: event.occurrence_date
      }
    })
    .filter(Boolean) as DueTaskEntry[]

  const merged = [...regularEntries, ...movedEntries]

  const unique = new Map<string, DueTaskEntry>()
  merged.forEach(entry => {
    if (!unique.has(entry.task.id)) {
      unique.set(entry.task.id, entry)
    }
  })

  return Array.from(unique.values())
}

export function getOccurrenceStatusForDate(
  taskId: string,
  date: string,
  events: Array<Pick<TaskHistoryItem, 'task_id' | 'occurrence_date' | 'status'>>
): EventStatus | undefined {
  const statusMap = getOccurrenceStatusMap(events)
  return statusMap.get(makeOccurrenceKey(taskId, date))
}

const DOW_LABELS = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']

const SKIP_POLICY_LABELS: Record<string, string> = {
  move: 'перенос',
  overdue: 'просрочка',
  skip: 'пропуск',
}

/**
 * Returns a human-readable description of the task's recurrence rule
 * matching the iCalendar RRULE that the backend generates via build_rrule().
 *
 * Examples:
 *   once    → "Разово, 15 апр"
 *   daily   → "Ежедневно"
 *   weekly  → "Еженедельно: Пн, Ср, Пт"
 *   monthly → "Ежемесячно, 15-го"
 *   custom  → "Каждые 3 дня"
 *
 * Also includes skip-policy and window info when present.
 */
export function buildRRuleDescription(task: Task): string {
  const parts: string[] = []

  switch (task.frequency) {
    case 'once': {
      const d = toDateObj(task.start_date)
      parts.push(`Разово, ${d.getDate()} ${d.toLocaleString('ru', { month: 'short' })}`)
      break
    }
    case 'daily':
      parts.push('Ежедневно')
      break
    case 'weekly': {
      const start = toDateObj(task.start_date)
      const startDow = start.getDay() === 0 ? 6 : start.getDay() - 1
      const days = task.days_of_week ?? [startDow]
      const dayNames = [...days].sort((a, b) => a - b).map(d => DOW_LABELS[d]).join(', ')
      parts.push(`Еженедельно: ${dayNames}`)
      break
    }
    case 'monthly': {
      const d = toDateObj(task.start_date)
      parts.push(`Ежемесячно, ${d.getDate()}-го`)
      break
    }
    case 'custom':
      parts.push(`Каждые ${task.custom_interval_days ?? 1} дн.`)
      break
  }

  if (task.window_days > 0) {
    parts.push(`окно ${task.window_days} дн.`)
  }

  if (task.frequency !== 'once') {
    parts.push(`при пропуске: ${SKIP_POLICY_LABELS[task.skip_policy] ?? task.skip_policy}`)
  }

  return parts.join(' · ')
}