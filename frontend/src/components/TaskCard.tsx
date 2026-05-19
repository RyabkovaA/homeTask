import { useState } from 'react'
import { Check, X, ArrowRight, Lightbulb } from 'lucide-react'
import type { Task, Room, EventStatus } from '../types'
import { Badge } from './ui/Badge'
import { Spinner } from './ui/Spinner'

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

interface TaskActionPayload {
  status: EventStatus
  moved_to?: string | null
}

interface TaskCardProps {
  task: Task
  room?: Room
  occurrenceDate?: string
  existingStatus?: EventStatus
  onAction: (payload: TaskActionPayload) => void
  loading?: boolean
  onGetAdvice?: () => void
  adviceOpen?: boolean
  adviceLoading?: boolean
  advicePanel?: React.ReactNode
}

function getTomorrow() {
  const d = new Date()
  d.setDate(d.getDate() + 1)
  return d.toISOString().slice(0, 10)
}

export function TaskCard({ task, room, existingStatus, onAction, loading, onGetAdvice, adviceOpen, adviceLoading, advicePanel }: TaskCardProps) {
  const [showMoveForm, setShowMoveForm] = useState(false)
  const [moveDate, setMoveDate] = useState(getTomorrow())

  const isDone = existingStatus === 'done'
  const isSkipped = existingStatus === 'skipped'
  const isMoved = existingStatus === 'moved'

  const handleMoveConfirm = () => {
    if (!moveDate) return
    onAction({ status: 'moved', moved_to: moveDate })
    setShowMoveForm(false)
  }

  return (
    <div className={`card flex gap-4 transition-opacity ${isDone ? 'opacity-60' : ''}`}>
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

          {!isDone && !isSkipped && !isMoved && (
            <div className="flex items-center gap-1 flex-shrink-0">
              {onGetAdvice && (
                <button
                  onClick={onGetAdvice}
                  disabled={adviceLoading}
                  title="Получить совет из базы знаний"
                  className={`w-8 h-8 rounded-lg flex items-center justify-center transition-colors disabled:opacity-50 ${
                    adviceOpen ? 'bg-forest-200 text-forest-700' : 'bg-beige-100 hover:bg-forest-100 text-neutral-400 hover:text-forest-600'
                  }`}
                >
                  {adviceLoading ? <Spinner className="w-3.5 h-3.5" /> : <Lightbulb size={14} />}
                </button>
              )}

              <button
                onClick={() => onAction({ status: 'done' })}
                disabled={loading}
                title="Выполнено"
                className="w-8 h-8 rounded-lg bg-forest-100 hover:bg-forest-200 text-forest-600 flex items-center justify-center transition-colors disabled:opacity-50"
              >
                <Check size={14} />
              </button>

              <button
                onClick={() => onAction({ status: 'skipped' })}
                disabled={loading}
                title="Пропустить"
                className="w-8 h-8 rounded-lg bg-beige-200 hover:bg-beige-300 text-neutral-500 flex items-center justify-center transition-colors disabled:opacity-50"
              >
                <X size={14} />
              </button>

              <button
                onClick={() => setShowMoveForm(v => !v)}
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
          {isMoved && (
            <span className="text-xs text-amber-600 font-medium flex-shrink-0">Перенесено</span>
          )}
        </div>

        {advicePanel}

        {showMoveForm && !isDone && !isSkipped && !isMoved && (
          <div className="mt-3 pt-3 border-t border-beige-200 animate-fade-in">
            <p className="text-xs font-medium text-neutral-500 uppercase tracking-wide mb-2">
              Перенести задачу
            </p>

            <div className="flex flex-col sm:flex-row gap-2 sm:items-center">
              <input
                type="date"
                className="input"
                value={moveDate}
                min={new Date().toISOString().slice(0, 10)}
                onChange={e => setMoveDate(e.target.value)}
              />

              <div className="flex gap-2">
                <button
                  onClick={handleMoveConfirm}
                  disabled={loading || !moveDate}
                  className="btn-primary px-4 py-2 text-sm"
                >
                  Сохранить
                </button>

                <button
                  onClick={() => setShowMoveForm(false)}
                  disabled={loading}
                  className="btn-secondary px-4 py-2 text-sm"
                >
                  Отмена
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}