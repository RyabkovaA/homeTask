import { format, isToday, isTomorrow, isYesterday, parseISO } from 'date-fns'
import { ru } from 'date-fns/locale'

export function formatDate(dateStr: string): string {
  const date = parseISO(dateStr)
  if (isToday(date)) return 'Сегодня'
  if (isTomorrow(date)) return 'Завтра'
  if (isYesterday(date)) return 'Вчера'
  return format(date, 'd MMMM', { locale: ru })
}

export function formatDateFull(dateStr: string): string {
  return format(parseISO(dateStr), 'd MMMM yyyy', { locale: ru })
}

export function todayStr(): string {
  return format(new Date(), 'yyyy-MM-dd')
}

export function toDateStr(date: Date): string {
  return format(date, 'yyyy-MM-dd')
}
