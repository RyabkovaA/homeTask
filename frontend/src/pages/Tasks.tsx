import { useState, useMemo } from 'react'
import { Plus, Search, Pencil, Trash2 } from 'lucide-react'
import { useTasks, useDeleteTask } from '../hooks/useTasks'
import { useRooms } from '../hooks/useRooms'
import { useMembers } from '../hooks/useMembers'
import { TaskForm } from '../components/TaskForm'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { Spinner } from '../components/ui/Spinner'
import type { Task, Priority } from '../types'
import toast from 'react-hot-toast'

const PRIORITY_LABELS: Record<Priority, string> = { low: 'Низкий', medium: 'Средний', high: 'Высокий' }
const PRIORITY_VARIANTS: Record<Priority, 'default' | 'success' | 'warning' | 'danger'> = {
  low: 'default', medium: 'warning', high: 'danger'
}
const FREQ_LABELS: Record<string, string> = {
  once: 'Разово', daily: 'Ежедневно', weekly: 'Еженедельно', monthly: 'Ежемесячно', custom: 'Кастомно'
}

export default function Tasks() {
  const [search, setSearch] = useState('')
  const [roomFilter, setRoomFilter] = useState('')
  const [priorityFilter, setPriorityFilter] = useState<Priority | ''>('')
  const [formOpen, setFormOpen] = useState(false)
  const [editTask, setEditTask] = useState<Task | null>(null)

  const { data: tasks = [], isLoading } = useTasks()
  const { data: rooms = [] } = useRooms()
  const { data: members = [] } = useMembers()
  const deleteTask = useDeleteTask()

  const roomMap = useMemo(() => new Map(rooms.map(r => [r.id, r])), [rooms])
  const memberMap = useMemo(() => new Map(members.map(m => [m.id, m])), [members])

  const filtered = useMemo(() => tasks.filter(t => {
    if (search && !t.title.toLowerCase().includes(search.toLowerCase())) return false
    if (roomFilter && t.room_id !== roomFilter) return false
    if (priorityFilter && t.priority !== priorityFilter) return false
    return true
  }), [tasks, search, roomFilter, priorityFilter])

  const handleDelete = async (task: Task) => {
    if (!confirm(`Удалить "${task.title}"?`)) return
    try {
      await deleteTask.mutateAsync(task.id)
      toast.success('Задача удалена')
    } catch {
      toast.error('Ошибка удаления')
    }
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h1 className="font-display text-2xl text-forest-500">Задачи</h1>
      </div>

      {/* Filters */}
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
      </div>

      {/* Task list */}
      {isLoading ? (
        <div className="flex justify-center py-12"><Spinner className="w-8 h-8" /></div>
      ) : filtered.length === 0 ? (
        <div className="card text-center text-neutral-400 py-10">
          <p className="text-3xl mb-2">📝</p>
          <p>Задач не найдено</p>
        </div>
      ) : (
        <div className="space-y-2">
          {filtered.map(task => {
            const room = task.room_id ? roomMap.get(task.room_id) : undefined
            const assignee = task.assignee_id ? memberMap.get(task.assignee_id) : undefined
            return (
              <div key={task.id} className="card flex items-center gap-4 hover:shadow-hover transition-shadow">
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-sm text-neutral-800 truncate">{task.title}</p>
                  <div className="flex items-center gap-2 mt-1 flex-wrap">
                    {room && <span className="text-xs text-neutral-500">{room.icon} {room.name}</span>}
                    <Badge variant={PRIORITY_VARIANTS[task.priority]}>{PRIORITY_LABELS[task.priority]}</Badge>
                    <Badge>{FREQ_LABELS[task.frequency]}</Badge>
                    {assignee && (
                      <span className="text-xs text-neutral-400">{assignee.user?.name ?? 'N/A'}</span>
                    )}
                  </div>
                </div>
                <div className="flex gap-1 flex-shrink-0">
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
            )
          })}
        </div>
      )}

      {/* FAB */}
      <button
        onClick={() => { setEditTask(null); setFormOpen(true) }}
        className="fixed bottom-20 right-6 md:bottom-8 w-14 h-14 bg-forest-400 hover:bg-forest-500 text-white rounded-full shadow-hover flex items-center justify-center transition-all active:scale-95"
      >
        <Plus size={24} />
      </button>

      <TaskForm
        open={formOpen}
        onClose={() => { setFormOpen(false); setEditTask(null) }}
        task={editTask}
      />
    </div>
  )
}
