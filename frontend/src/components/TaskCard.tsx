import { Check, X, ArrowRight } from 'lucide-react'
import type { Task, Room, EventStatus } from '../types'
import { Badge } from './ui/Badge'

const PRIORITY_COLORS: Record<string, string> = {
  high: '#4A7C59',
  medium: '#8DB596',
  low: '#DDD3BC',
}

const FREQ_LABELS: Record<string, string> = {
  once: 'Разово',
  daily: 'Ежедневно',
  weekly: 'Еженедельно',
  monthly: 'Ежемесячно',
  custom: 'Кастомно',
}

interface TaskCardProps {
  task: Task
  room?: Room
  occurrenceDate?: string
  existingStatus?: EventStatus
  onAction: (status: EventStatus) => void
  loading?: boolean
}

export function TaskCard({ task, room, existingStatus, onAction, loading }: TaskCardProps) {
  const isDone = existingStatus === 'done'
  const isSkipped = existingStatus === 'skipped'

  return (
    <div className={`card flex gap-4 transition-opacity ${isDone ? 'opacity-60' : ''}`}>
      {/* Priority stripe */}
      <div
        className="w-1 rounded-full flex-shrink-0"
        style={{ backgroundColor: PRIORITY_COLORS[task.priority] }}
      />

      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0">
            <p className={`font-medium text-sm ${isDone ? 'line-through text-neutral-400' : 'text-neutral-800'}`}>
              {task.title}
            </p>
            <div className="flex items-center gap-2 mt-1 flex-wrap">
              {room && (
                <span className="text-xs text-neutral-500 flex items-center gap-1">
                  {room.icon} {room.name}
                </span>
              )}
              <Badge variant="default">{FREQ_LABELS[task.frequency]}</Badge>
            </div>
          </div>

          {/* Action buttons */}
          {!isDone && !isSkipped && (
            <div className="flex items-center gap-1 flex-shrink-0">
              <button
                onClick={() => onAction('done')}
                disabled={loading}
                title="Выполнено"
                className="w-8 h-8 rounded-lg bg-forest-100 hover:bg-forest-200 text-forest-600 flex items-center justify-center transition-colors disabled:opacity-50"
              >
                <Check size={14} />
              </button>
              <button
                onClick={() => onAction('skipped')}
                disabled={loading}
                title="Пропустить"
                className="w-8 h-8 rounded-lg bg-beige-200 hover:bg-beige-300 text-neutral-500 flex items-center justify-center transition-colors disabled:opacity-50"
              >
                <X size={14} />
              </button>
              <button
                onClick={() => onAction('moved')}
                disabled={loading}
                title="Перенести"
                className="w-8 h-8 rounded-lg bg-amber-100 hover:bg-amber-200 text-amber-600 flex items-center justify-center transition-colors disabled:opacity-50"
              >
                <ArrowRight size={14} />
              </button>
            </div>
          )}

          {isDone && (
            <span className="text-xs text-forest-400 font-medium flex-shrink-0">✓ Готово</span>
          )}
          {isSkipped && (
            <span className="text-xs text-neutral-400 font-medium flex-shrink-0">Пропущено</span>
          )}
        </div>
      </div>
    </div>
  )
}
