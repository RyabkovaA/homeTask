import type { Task } from '../types'

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
      // JS getDay: 0=Sun, convert to Mon=0..Sun=6
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
