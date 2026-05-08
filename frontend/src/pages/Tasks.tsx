import { useState, useMemo } from 'react'
import { Plus, Search, Pencil, Trash2, Check, ArrowRight, Lightbulb, Sparkles, X, User } from 'lucide-react'
import { useTasks, useDeleteTask } from '../hooks/useTasks'
import { useRooms } from '../hooks/useRooms'
import { useMembers } from '../hooks/useMembers'
import { useCreateEvent, useEvents } from '../hooks/useEvents'
import { useTaskRagAdvice, useSuggestTasks } from '../hooks/useRag'
import { useAuthStore } from '../store/authStore'
import { TaskForm } from '../components/TaskForm'
import { AdvicePanel } from '../components/AdvicePanel'
import { Badge } from '../components/ui/Badge'
import { Spinner } from '../components/ui/Spinner'
import type { Task, Priority, RagAdvice, SuggestedTask } from '../types'
import toast from 'react-hot-toast'
import { format } from 'date-fns'
import { ru } from 'date-fns/locale'
import {
  getDueTaskEntries,
  getOccurrenceStatusMap,
  buildRRuleDescription,
} from '../utils/recurrence'

const PRIORITY_LABELS: Record<Priority, string> = { low: 'Низкий', medium: 'Средний', high: 'Высокий' }
const PRIORITY_VARIANTS: Record<Priority, 'default' | 'success' | 'warning' | 'danger'> = {
  low: 'default',
  medium: 'warning',
  high: 'danger'
}

function getTomorrow() {
  const d = new Date()
  d.setDate(d.getDate() + 1)
  return d.toISOString().slice(0, 10)
}

function addDays(dateStr: string, days: number) {
  const d = new Date(dateStr + 'T00:00:00')
  d.setDate(d.getDate() + days)
  return d.toISOString().slice(0, 10)
}

export default function Tasks() {
  const today = new Date().toISOString().slice(0, 10)
  const monthAgo = addDays(today, -30)
  const currentMemberId = useAuthStore(s => s.memberId)

  const [search, setSearch] = useState('')
  const [roomFilter, setRoomFilter] = useState('')
  const [priorityFilter, setPriorityFilter] = useState<Priority | ''>('')
  const [onlyMine, setOnlyMine] = useState(false)
  const [formOpen, setFormOpen] = useState(false)
  const [editTask, setEditTask] = useState<Task | null>(null)
  const [moveTaskId, setMoveTaskId] = useState<string | null>(null)
  const [moveDate, setMoveDate] = useState(getTomorrow())
  // RAG advice state: taskId → advice result (null while loading)
  const [adviceOpenId, setAdviceOpenId] = useState<string | null>(null)
  const [adviceMap, setAdviceMap] = useState<Record<string, RagAdvice>>({})
  const [adviceLoadingId, setAdviceLoadingId] = useState<string | null>(null)
  const [adviceErrorId, setAdviceErrorId] = useState<string | null>(null)
  const [suggestOpen, setSuggestOpen] = useState(false)
  const [suggestions, setSuggestions] = useState<SuggestedTask[]>([])
  const [suggestSeason, setSuggestSeason] = useState('')
  const [prefillTitle, setPrefillTitle] = useState<string | undefined>(undefined)

  const { data: tasks = [], isLoading } = useTasks()
  const { data: rooms = [] } = useRooms()
  const { data: members = [] } = useMembers()
  const { data: recentEvents = [] } = useEvents({ fromDate: monthAgo, toDate: today })
  const deleteTask = useDeleteTask()
  const createEvent = useCreateEvent()
  const getAdvice = useTaskRagAdvice()
  const suggestMutation = useSuggestTasks()

  const roomMap = useMemo(() => new Map(rooms.map(r => [r.id, r])), [rooms])
  const memberMap = useMemo(() => new Map(members.map(m => [m.id, m])), [members])

  const todayDueEntries = useMemo(
    () => getDueTaskEntries(tasks, recentEvents, today),
    [tasks, recentEvents, today]
  )

  const todayDueMap = useMemo(() => {
    const map = new Map<string, { occurrenceDate: string }>()
    todayDueEntries.forEach(entry => {
      map.set(entry.task.id, {
        occurrenceDate: entry.originalOccurrenceDate ?? entry.date
      })
    })
    return map
  }, [todayDueEntries])

  const occurrenceStatusMap = useMemo(
    () => getOccurrenceStatusMap(recentEvents),
    [recentEvents]
  )

  const doneToday = useMemo(() => new Set(
    todayDueEntries
      .filter(e => occurrenceStatusMap.get(`${e.task.id}_${today}`) === 'done')
      .map(e => e.task.id)
  ), [todayDueEntries, occurrenceStatusMap, today])

  const sortByDone = (list: Task[]) =>
    [...list].sort((a, b) => (doneToday.has(a.id) ? 1 : 0) - (doneToday.has(b.id) ? 1 : 0))

  const { myTasks, canDoTasks } = useMemo(() => {
    const base = tasks.filter(t => {
      if (search && !t.title.toLowerCase().includes(search.toLowerCase())) return false
      if (roomFilter && t.room_id !== roomFilter) return false
      if (priorityFilter && t.priority !== priorityFilter) return false
      return true
    })
    // My tasks: no assignee OR assigned to me
    const my = base.filter(t => !t.assignee_id || t.assignee_id === currentMemberId)
    // Can-do: assigned to someone else
    const canDo = onlyMine ? [] : base.filter(t => t.assignee_id && t.assignee_id !== currentMemberId)
    return { myTasks: sortByDone(my), canDoTasks: sortByDone(canDo) }
  }, [tasks, search, roomFilter, priorityFilter, onlyMine, currentMemberId, doneToday])

  const handleDelete = async (task: Task) => {
    if (!confirm(`Удалить "${task.title}"?`)) return
    try {
      await deleteTask.mutateAsync(task.id)
      toast.success('Задача удалена')
    } catch {
      toast.error('Ошибка удаления')
    }
  }

  const handleComplete = async (task: Task, occurrenceDate: string) => {
    try {
      await createEvent.mutateAsync({
        task_id: task.id,
        occurrence_date: occurrenceDate,
        status: 'done'
      })
      toast.success('Задача отмечена выполненной')
    } catch {
      toast.error('Не удалось отметить задачу выполненной')
    }
  }

  const handleMove = async (taskId: string, occurrenceDate: string) => {
    try {
      await createEvent.mutateAsync({
        task_id: taskId,
        occurrence_date: occurrenceDate,
        status: 'moved',
        moved_to: moveDate
      })
      toast.success(`Задача перенесена на ${format(new Date(moveDate), 'd MMMM', { locale: ru })}`)
      setMoveTaskId(null)
      setMoveDate(getTomorrow())
    } catch {
      toast.error('Не удалось перенести задачу')
    }
  }

  const handleSuggest = async () => {
    setSuggestOpen(true)
    if (suggestions.length > 0) return
    try {
      const res = await suggestMutation.mutateAsync()
      setSuggestions(res.suggestions)
      setSuggestSeason(res.season)
    } catch {
      toast.error('Не удалось получить предложения')
    }
  }

  const handleToggleAdvice = async (task: Task) => {
    // Toggle off
    if (adviceOpenId === task.id) {
      setAdviceOpenId(null)
      return
    }
    setAdviceOpenId(task.id)
    setAdviceErrorId(null)

    // Already loaded — just show
    if (adviceMap[task.id]) return

    setAdviceLoadingId(task.id)
    try {
      const advice = await getAdvice.mutateAsync(task.id)
      setAdviceMap(prev => ({ ...prev, [task.id]: advice }))
    } catch {
      setAdviceErrorId(task.id)
      toast.error('Не удалось получить совет')
    } finally {
      setAdviceLoadingId(null)
    }
  }

  const renderTask = (task: Task) => {
    const room = task.room_id ? roomMap.get(task.room_id) : undefined
    const assignee = task.assignee_id ? memberMap.get(task.assignee_id) : undefined
    const dueInfo = todayDueMap.get(task.id)
    const todayStatus = occurrenceStatusMap.get(`${task.id}_${today}`)
    const canActToday = !!dueInfo && todayStatus !== 'done' && todayStatus !== 'skipped' && todayStatus !== 'moved'
    const adviceOpen = adviceOpenId === task.id
    const adviceLoading = adviceLoadingId === task.id
    const adviceError = adviceErrorId === task.id

    return (
      <div key={task.id} className="card hover:shadow-hover transition-shadow">
        <div className="flex items-center gap-4">
          <div className="flex-1 min-w-0">
            <p className={`font-medium text-sm truncate ${todayStatus === 'done' ? 'line-through text-neutral-400' : 'text-neutral-800'}`}>
              {task.title}
            </p>
            <div className="flex items-center gap-2 mt-1 flex-wrap">
              {room && <span className="text-xs text-neutral-500">{room.icon} {room.name}</span>}
              <Badge variant={PRIORITY_VARIANTS[task.priority]}>{PRIORITY_LABELS[task.priority]}</Badge>
              <span className="text-xs text-neutral-400">{buildRRuleDescription(task)}</span>
              {assignee && <span className="text-xs text-neutral-400">{assignee.user?.name ?? 'N/A'}</span>}
              {todayStatus === 'done' && <Badge variant="success">Выполнено сегодня</Badge>}
              {todayStatus === 'moved' && <Badge variant="info">Перенесено</Badge>}
              {!todayStatus && dueInfo && <Badge variant="warning">Актуально на сегодня</Badge>}
            </div>
          </div>

          <div className="flex gap-1 flex-shrink-0">
            <button
              onClick={() => handleToggleAdvice(task)}
              disabled={adviceLoading}
              title="Получить совет из базы знаний"
              className={`w-8 h-8 rounded-lg flex items-center justify-center transition-colors disabled:opacity-50 ${
                adviceOpen ? 'bg-forest-200 text-forest-700' : 'bg-beige-100 hover:bg-forest-100 text-neutral-400 hover:text-forest-600'
              }`}
            >
              {adviceLoading ? <Spinner className="w-3.5 h-3.5" /> : <Lightbulb size={14} />}
            </button>

            {canActToday && dueInfo && (
              <>
                <button
                  onClick={() => handleComplete(task, dueInfo.occurrenceDate)}
                  disabled={createEvent.isPending}
                  title="Отметить выполненной"
                  className="w-8 h-8 rounded-lg bg-forest-100 hover:bg-forest-200 text-forest-600 flex items-center justify-center transition-colors disabled:opacity-50"
                >
                  <Check size={14} />
                </button>
                <button
                  onClick={() => { setMoveTaskId(prev => prev === task.id ? null : task.id); setMoveDate(getTomorrow()) }}
                  disabled={createEvent.isPending}
                  title="Перенести"
                  className="w-8 h-8 rounded-lg bg-amber-100 hover:bg-amber-200 text-amber-600 flex items-center justify-center transition-colors disabled:opacity-50"
                >
                  <ArrowRight size={14} />
                </button>
              </>
            )}

            <button
              onClick={() => { setEditTask(task); setFormOpen(true) }}
              className="w-8 h-8 rounded-lg bg-beige-200 hover:bg-beige-300 text-neutral-500 flex items-center justify-center transition-colors"
            >
              <Pencil size={14} />
            </button>
            <button
              onClick={() => handleDelete(task)}
              className="w-8 h-8 rounded-lg bg-red-100 hover:bg-red-200 text-red-500 flex items-center justify-center transition-colors"
            >
              <Trash2 size={14} />
            </button>
          </div>
        </div>

        {adviceOpen && (
          <AdvicePanel advice={adviceMap[task.id] ?? null} isLoading={adviceLoading} error={adviceError} compact={false} />
        )}

        {moveTaskId === task.id && dueInfo && (
          <div className="mt-3 pt-3 border-t border-beige-200 animate-fade-in">
            <p className="text-xs font-medium text-neutral-500 uppercase tracking-wide mb-2">Перенести задачу</p>
            <div className="flex flex-col sm:flex-row gap-2 sm:items-center">
              <input type="date" className="input" value={moveDate} min={today} onChange={e => setMoveDate(e.target.value)} />
              <div className="flex gap-2">
                <button onClick={() => handleMove(task.id, dueInfo.occurrenceDate)} disabled={createEvent.isPending || !moveDate} className="btn-primary px-4 py-2 text-sm">Сохранить</button>
                <button onClick={() => setMoveTaskId(null)} disabled={createEvent.isPending} className="btn-secondary px-4 py-2 text-sm">Отмена</button>
              </div>
            </div>
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h1 className="font-display text-2xl text-forest-500">Задачи</h1>
        <button
          onClick={handleSuggest}
          disabled={suggestMutation.isPending}
          className="flex items-center gap-2 px-3 py-2 rounded-xl bg-forest-50 border border-forest-200 text-forest-600 text-sm font-medium hover:bg-forest-100 transition-colors disabled:opacity-50"
        >
          {suggestMutation.isPending ? <Spinner className="w-3.5 h-3.5" /> : <Sparkles size={14} />}
          Предложить задачи
        </button>
      </div>

      <div className="flex flex-wrap gap-3">
        <div className="relative flex-1 min-w-48">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-neutral-400" />
          <input
            className="input pl-9"
            placeholder="Поиск задач..."
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
        </div>

        <select className="input w-40" value={roomFilter} onChange={e => setRoomFilter(e.target.value)}>
          <option value="">Все комнаты</option>
          {rooms.map(r => <option key={r.id} value={r.id}>{r.icon} {r.name}</option>)}
        </select>

        <div className="flex gap-1">
          {(['', 'low', 'medium', 'high'] as (Priority | '')[]).map(p => (
            <button
              key={p}
              onClick={() => setPriorityFilter(p)}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                priorityFilter === p ? 'bg-forest-400 text-white' : 'bg-beige-200 text-neutral-600 hover:bg-beige-300'
              }`}
            >
              {p === '' ? 'Все' : PRIORITY_LABELS[p]}
            </button>
          ))}
        </div>

        <button
          onClick={() => setOnlyMine(v => !v)}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
            onlyMine ? 'bg-forest-400 text-white' : 'bg-beige-200 text-neutral-600 hover:bg-beige-300'
          }`}
          title="Показать только задачи, назначенные мне"
        >
          <User size={13} />
          Только мои
        </button>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-12"><Spinner className="w-8 h-8" /></div>
      ) : myTasks.length === 0 && canDoTasks.length === 0 ? (
        <div className="card text-center text-neutral-400 py-10">
          <p className="text-3xl mb-2">📝</p>
          <p>Задач не найдено</p>
        </div>
      ) : (
        <>
          {myTasks.length > 0 && (
            <section>
              <h2 className="font-display text-sm text-neutral-500 uppercase tracking-wide mb-2">Мои задачи</h2>
              <div className="space-y-2">{myTasks.map(renderTask)}</div>
            </section>
          )}
          {canDoTasks.length > 0 && (
            <section>
              <h2 className="font-display text-sm text-neutral-500 uppercase tracking-wide mb-2 mt-4">Можно сделать</h2>
              <div className="space-y-2">{canDoTasks.map(renderTask)}</div>
            </section>
          )}
        </>
      )}

      <button
        onClick={() => { setEditTask(null); setFormOpen(true) }}
        className="fixed bottom-20 right-6 md:bottom-8 w-14 h-14 bg-forest-400 hover:bg-forest-500 text-white rounded-full shadow-hover flex items-center justify-center transition-all active:scale-95"
      >
        <Plus size={24} />
      </button>

      <TaskForm
        open={formOpen}
        onClose={() => { setFormOpen(false); setEditTask(null); setPrefillTitle(undefined) }}
        task={editTask}
        prefillTitle={prefillTitle}
      />

      {/* Suggestions modal */}
      {suggestOpen && (
        <div className="fixed inset-0 bg-black/30 z-40 flex items-end md:items-center justify-center p-4">
          <div className="bg-beige-50 rounded-2xl shadow-xl w-full max-w-lg max-h-[80vh] flex flex-col animate-fade-in">
            <div className="flex items-center justify-between px-5 py-4 border-b border-beige-200">
              <div>
                <h2 className="font-display text-lg text-forest-500 font-semibold flex items-center gap-2">
                  <Sparkles size={18} /> Предложения задач
                </h2>
                {suggestSeason && (
                  <p className="text-xs text-neutral-400 mt-0.5">
                    Сезон: {suggestSeason === 'winter' ? 'Зима' : suggestSeason === 'spring' ? 'Весна' : suggestSeason === 'summer' ? 'Лето' : 'Осень'} · {suggestions.length} рекомендаций
                  </p>
                )}
              </div>
              <button
                onClick={() => setSuggestOpen(false)}
                className="w-8 h-8 rounded-xl bg-beige-200 hover:bg-beige-300 flex items-center justify-center text-neutral-500 transition-colors"
              >
                <X size={16} />
              </button>
            </div>

            <div className="overflow-y-auto flex-1 px-5 py-4 space-y-3">
              {suggestMutation.isPending ? (
                <div className="flex justify-center py-8"><Spinner className="w-6 h-6" /></div>
              ) : suggestions.length === 0 ? (
                <p className="text-center text-neutral-400 py-8">Нет предложений</p>
              ) : suggestions.map((s, i) => (
                <div key={i} className="rounded-xl border border-beige-200 bg-white p-3 space-y-1.5">
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-sm text-neutral-800">{s.title}</p>
                      <div className="flex items-center gap-2 mt-1 flex-wrap">
                        {s.room_name && <span className="text-xs text-neutral-500">📍 {s.room_name}</span>}
                        <span className="text-xs text-neutral-400">{s.effort_hours}ч</span>
                        <span className={`text-xs px-1.5 py-0.5 rounded-md font-medium ${
                          s.source === 'llm' ? 'bg-purple-100 text-purple-600' :
                          s.source === 'gap' ? 'bg-amber-100 text-amber-600' :
                          'bg-forest-100 text-forest-600'
                        }`}>
                          {s.source === 'llm' ? 'AI' : s.source === 'gap' ? 'Пробел' : 'Сезон'}
                        </span>
                      </div>
                      <p className="text-xs text-neutral-500 mt-1">{s.reason}</p>
                    </div>
                    <button
                      onClick={() => {
                        setSuggestOpen(false)
                        setEditTask(null)
                        setPrefillTitle(s.title)
                        setFormOpen(true)
                      }}
                      className="flex-shrink-0 px-3 py-1.5 rounded-lg bg-forest-400 hover:bg-forest-500 text-white text-xs font-medium transition-colors"
                    >
                      Добавить
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
