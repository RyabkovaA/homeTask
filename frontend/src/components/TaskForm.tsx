import { useState, useEffect } from 'react'
import { LayoutTemplate, X } from 'lucide-react'
import { Modal } from './ui/Modal'
import { Button } from './ui/Button'
import type { Task, TaskFormData, Priority, Frequency, SkipPolicy } from '../types'
import { useRooms } from '../hooks/useRooms'
import { useMembers } from '../hooks/useMembers'
import { useCreateTask, useUpdateTask } from '../hooks/useTasks'
import { getTemplatesForRoom, type TaskTemplate } from '../utils/taskTemplates'
import toast from 'react-hot-toast'

const DAYS = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
const FREQ_OPTIONS: { value: Frequency; label: string }[] = [
  { value: 'once', label: 'Разово' },
  { value: 'daily', label: 'Ежедневно' },
  { value: 'weekly', label: 'Еженедельно' },
  { value: 'monthly', label: 'Ежемесячно' },
  { value: 'custom', label: 'Кастомный' },
]

const FREQ_SHORT: Record<Frequency, string> = {
  once: 'Разово',
  daily: 'Ежедневно',
  weekly: 'Еженедельно',
  monthly: 'Ежемесячно',
  custom: 'Интервал',
}

const PRIORITY_LABELS: Record<Priority, string> = {
  low: '🟢 Низкий',
  medium: '🟡 Средний',
  high: '🔴 Высокий',
}

interface TaskFormProps {
  open: boolean
  onClose: () => void
  task?: Task | null
}

const defaultForm: TaskFormData = {
  title: '',
  description: '',
  room_id: '',
  assignee_id: '',
  priority: 'medium',
  frequency: 'once',
  skip_policy: 'overdue',
  start_date: new Date().toISOString().slice(0, 10),
  days_of_week: [],
  custom_interval_days: 7,
  window_days: 0,
  effort_hours: 1.0,
}

function TemplateCard({
  tpl,
  onSelect,
}: {
  tpl: TaskTemplate
  onSelect: (t: TaskTemplate) => void
}) {
  return (
    <button
      type="button"
      onClick={() => onSelect(tpl)}
      className="w-full text-left px-3 py-2.5 rounded-xl border border-beige-200 bg-beige-50 hover:border-forest-300 hover:bg-forest-50 transition-colors group"
    >
      <div className="flex items-start justify-between gap-2">
        <span className="text-sm font-medium text-neutral-800 group-hover:text-forest-700 leading-snug">
          {tpl.title}
        </span>
        <span className="flex-shrink-0 text-xs text-neutral-400 mt-0.5">
          {FREQ_SHORT[tpl.frequency]}
        </span>
      </div>
      <div className="flex items-center gap-2 mt-1">
        <span className="text-xs text-neutral-500">{PRIORITY_LABELS[tpl.priority]}</span>
        <span className="text-xs text-neutral-400">{tpl.effort_hours}ч</span>
        {tpl.description && (
          <span className="text-xs text-neutral-400 truncate">{tpl.description.slice(0, 50)}{tpl.description.length > 50 ? '…' : ''}</span>
        )}
      </div>
    </button>
  )
}

export function TaskForm({ open, onClose, task }: TaskFormProps) {
  const [form, setForm] = useState<TaskFormData>(defaultForm)
  const [showTemplates, setShowTemplates] = useState(false)
  const { data: rooms = [] } = useRooms()
  const { data: members = [] } = useMembers()
  const createTask = useCreateTask()
  const updateTask = useUpdateTask()

  useEffect(() => {
    if (task) {
      setForm({
        title: task.title,
        description: task.description,
        room_id: task.room_id ?? '',
        assignee_id: task.assignee_id ?? '',
        priority: task.priority,
        frequency: task.frequency,
        skip_policy: task.skip_policy,
        start_date: task.start_date,
        days_of_week: task.days_of_week ?? [],
        custom_interval_days: task.custom_interval_days ?? 7,
        window_days: task.window_days ?? 0,
        effort_hours: task.effort_hours ?? 1.0,
      })
    } else {
      setForm(defaultForm)
    }
    setShowTemplates(false)
  }, [task, open])

  const set = (key: keyof TaskFormData, val: unknown) =>
    setForm(f => ({ ...f, [key]: val }))

  const toggleDay = (d: number) => {
    const days = form.days_of_week.includes(d)
      ? form.days_of_week.filter(x => x !== d)
      : [...form.days_of_week, d]
    set('days_of_week', days)
  }

  const applyTemplate = (tpl: TaskTemplate) => {
    setForm(f => ({
      ...f,
      title: tpl.title,
      description: tpl.description ?? '',
      priority: tpl.priority,
      frequency: tpl.frequency,
      skip_policy: tpl.skip_policy,
      days_of_week: tpl.days_of_week ?? [],
      custom_interval_days: tpl.custom_interval_days ?? 7,
      window_days: tpl.window_days ?? 0,
      effort_hours: tpl.effort_hours,
    }))
    setShowTemplates(false)
  }

  const selectedRoom = rooms.find(r => r.id === form.room_id)
  const templates = selectedRoom ? getTemplatesForRoom(selectedRoom.name) : []

  const handleSubmit = async () => {
    if (!form.title.trim()) return toast.error('Введите название задачи')
    const payload: Partial<TaskFormData> = {
      ...form,
      room_id: form.room_id || undefined,
      assignee_id: form.assignee_id || undefined,
      days_of_week: form.frequency === 'weekly' ? form.days_of_week : undefined,
      custom_interval_days: form.frequency === 'custom' ? form.custom_interval_days : undefined,
    } as Partial<TaskFormData>

    try {
      if (task) {
        await updateTask.mutateAsync({ taskId: task.id, data: payload })
        toast.success('Задача обновлена')
      } else {
        await createTask.mutateAsync(payload)
        toast.success('Задача создана')
      }
      onClose()
    } catch {
      toast.error('Ошибка сохранения задачи')
    }
  }

  return (
    <Modal open={open} onClose={onClose} title={task ? 'Редактировать задачу' : 'Новая задача'}>
      <div className="space-y-4">

        {/* Комната */}
        <div>
          <label className="label">Комната</label>
          <select
            className="input"
            value={form.room_id}
            onChange={e => {
              set('room_id', e.target.value)
              setShowTemplates(false)
            }}
          >
            <option value="">— Без комнаты —</option>
            {rooms.map(r => (
              <option key={r.id} value={r.id}>{r.icon} {r.name}</option>
            ))}
          </select>

          {/* Шаблоны задач */}
          {selectedRoom && (
            <div className="mt-2">
              <button
                type="button"
                onClick={() => setShowTemplates(v => !v)}
                className="inline-flex items-center gap-1.5 text-xs font-medium text-forest-600 hover:text-forest-700 transition-colors"
              >
                <LayoutTemplate size={13} />
                {showTemplates ? 'Скрыть шаблоны' : `Шаблоны задач для «${selectedRoom.name}»`}
              </button>

              {showTemplates && (
                <div className="mt-2 space-y-1.5 max-h-56 overflow-y-auto pr-1 animate-fade-in">
                  {templates.map((tpl, i) => (
                    <TemplateCard key={i} tpl={tpl} onSelect={applyTemplate} />
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Название */}
        <div>
          <div className="flex items-center justify-between mb-1">
            <label className="label mb-0">Название</label>
            {form.title && (
              <button
                type="button"
                onClick={() => set('title', '')}
                className="text-neutral-300 hover:text-neutral-500 transition-colors"
              >
                <X size={13} />
              </button>
            )}
          </div>
          <input
            className="input"
            value={form.title}
            onChange={e => set('title', e.target.value)}
            placeholder="Название задачи"
          />
        </div>

        {/* Описание */}
        <div>
          <label className="label">Описание</label>
          <textarea
            className="input resize-none h-20"
            value={form.description}
            onChange={e => set('description', e.target.value)}
            placeholder="Опционально"
          />
        </div>

        {/* Приоритет */}
        <div>
          <label className="label">Приоритет</label>
          <div className="flex gap-2">
            {(['low', 'medium', 'high'] as Priority[]).map(p => (
              <button
                key={p}
                type="button"
                onClick={() => set('priority', p)}
                className={`flex-1 py-2 rounded-xl text-sm font-medium border transition-all ${
                  form.priority === p
                    ? 'border-forest-400 bg-forest-50 text-forest-600'
                    : 'border-beige-200 bg-beige-100 text-neutral-600'
                }`}
              >
                {PRIORITY_LABELS[p]}
              </button>
            ))}
          </div>
        </div>

        {/* Частота */}
        <div>
          <label className="label">Частота</label>
          <div className="flex flex-wrap gap-1">
            {FREQ_OPTIONS.map(f => (
              <button
                key={f.value}
                type="button"
                onClick={() => set('frequency', f.value)}
                className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                  form.frequency === f.value
                    ? 'bg-forest-400 text-white'
                    : 'bg-beige-200 text-neutral-600 hover:bg-beige-300'
                }`}
              >
                {f.label}
              </button>
            ))}
          </div>

          {form.frequency === 'weekly' && (
            <div className="flex gap-1 mt-2">
              {DAYS.map((d, i) => (
                <button
                  key={i}
                  type="button"
                  onClick={() => toggleDay(i)}
                  className={`flex-1 py-1.5 rounded-lg text-xs font-medium transition-all ${
                    form.days_of_week.includes(i)
                      ? 'bg-forest-400 text-white'
                      : 'bg-beige-200 text-neutral-600'
                  }`}
                >
                  {d}
                </button>
              ))}
            </div>
          )}

          {form.frequency === 'custom' && (
            <div className="flex items-center gap-2 mt-2">
              <span className="text-sm text-neutral-500">Каждые</span>
              <input
                type="number"
                min={1}
                className="input w-20"
                value={form.custom_interval_days}
                onChange={e => set('custom_interval_days', parseInt(e.target.value) || 1)}
              />
              <span className="text-sm text-neutral-500">дней</span>
            </div>
          )}
        </div>

        {/* Политика пропуска */}
        <div>
          <label className="label">Политика пропуска</label>
          <div className="flex gap-2">
            {([['move', 'Перенести'], ['overdue', 'Просрочить'], ['skip', 'Пропустить']] as [SkipPolicy, string][]).map(([val, lbl]) => (
              <label key={val} className="flex items-center gap-1.5 cursor-pointer">
                <input
                  type="radio"
                  checked={form.skip_policy === val}
                  onChange={() => set('skip_policy', val)}
                  className="accent-forest-400"
                />
                <span className="text-sm">{lbl}</span>
              </label>
            ))}
          </div>
        </div>

        {/* Трудоёмкость */}
        <div>
          <label className="label">
            Трудоёмкость
            <span className="ml-1 text-xs text-neutral-400 font-normal">— примерное время выполнения</span>
          </label>
          <div className="flex items-center gap-2">
            <input
              type="number"
              min={0.1}
              max={24}
              step={0.1}
              className="input w-24"
              value={form.effort_hours}
              onChange={e => set('effort_hours', Math.max(0.1, parseFloat(e.target.value) || 1.0))}
            />
            <span className="text-sm text-neutral-500">ч</span>
          </div>
        </div>

        {/* Окно выполнения */}
        {form.frequency !== 'once' && (
          <div>
            <label className="label">
              Окно выполнения
              <span className="ml-1 text-xs text-neutral-400 font-normal">— сколько дней после плановой даты задача остаётся активной</span>
            </label>
            <div className="flex items-center gap-2">
              <input
                type="number"
                min={0}
                max={30}
                className="input w-20"
                value={form.window_days}
                onChange={e => set('window_days', Math.max(0, parseInt(e.target.value) || 0))}
              />
              <span className="text-sm text-neutral-500">дней</span>
            </div>
          </div>
        )}

        {/* Дата начала */}
        <div>
          <label className="label">Дата начала</label>
          <input
            type="date"
            className="input"
            value={form.start_date}
            onChange={e => set('start_date', e.target.value)}
          />
        </div>

        {/* Ответственный */}
        <div>
          <label className="label">Ответственный</label>
          <select className="input" value={form.assignee_id} onChange={e => set('assignee_id', e.target.value)}>
            <option value="">— Не назначен —</option>
            {members.map(m => (
              <option key={m.id} value={m.id}>{m.user?.name ?? m.id}</option>
            ))}
          </select>
        </div>

        <div className="flex gap-3 pt-2">
          <Button variant="secondary" onClick={onClose} className="flex-1">Отмена</Button>
          <Button
            onClick={handleSubmit}
            className="flex-1"
            disabled={createTask.isPending || updateTask.isPending}
          >
            {task ? 'Сохранить' : 'Создать'}
          </Button>
        </div>
      </div>
    </Modal>
  )
}
