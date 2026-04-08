import { useMemo } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ArrowLeft, ArrowRight, CheckSquare, Lightbulb } from 'lucide-react'
import { useRooms } from '../hooks/useRooms'
import { useTasks } from '../hooks/useTasks'
import { useAdvice } from '../hooks/useAdvice'
import { Badge } from '../components/ui/Badge'
import { Spinner } from '../components/ui/Spinner'

const PRIORITY_LABELS: Record<string, string> = {
  low: 'Низкий',
  medium: 'Средний',
  high: 'Высокий'
}

const PRIORITY_VARIANTS: Record<string, 'default' | 'info' | 'warning' | 'danger' | 'success'> = {
  low: 'default',
  medium: 'warning',
  high: 'danger'
}

const FREQUENCY_LABELS: Record<string, string> = {
  once: 'Разово',
  daily: 'Ежедневно',
  weekly: 'Еженедельно',
  monthly: 'Ежемесячно',
  custom: 'Кастомно'
}

export default function HouseRoom() {
  const { roomId = '' } = useParams()
  const { data: rooms = [], isLoading: roomsLoading } = useRooms()
  const { data: tasks = [], isLoading: tasksLoading } = useTasks()

  const room = useMemo(
    () => rooms.find(item => item.id === roomId) ?? null,
    [rooms, roomId]
  )

  const { data: advice = [], isLoading: adviceLoading } = useAdvice(room?.name)

  const roomTasks = useMemo(
    () => tasks.filter(task => task.room_id === roomId),
    [tasks, roomId]
  )

  const featuredAdvice = useMemo(
    () => advice.slice(0, 2),
    [advice]
  )

  if (roomsLoading || tasksLoading || (room && adviceLoading)) {
    return (
      <div className="flex justify-center py-12">
        <Spinner className="w-8 h-8" />
      </div>
    )
  }

  if (!room) {
    return (
      <div className="space-y-4 max-w-3xl mx-auto">
        <Link
          to="/house"
          className="inline-flex items-center gap-2 text-sm font-medium text-neutral-500 hover:text-forest-500 transition-colors"
        >
          <ArrowLeft size={16} />
          Назад к дому
        </Link>

        <div className="card text-center py-10">
          <p className="text-3xl mb-2">🏠</p>
          <h1 className="font-display text-xl text-neutral-800 mb-2">Комната не найдена</h1>
          <p className="text-sm text-neutral-500">Возможно, она была удалена или ссылка устарела.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6 max-w-3xl mx-auto">
      <div className="space-y-3">
        <Link
          to="/house"
          className="inline-flex items-center gap-2 text-sm font-medium text-neutral-500 hover:text-forest-500 transition-colors"
        >
          <ArrowLeft size={16} />
          Назад к дому
        </Link>

        <div className="card">
          <div className="flex items-center gap-4">
            <div
              className="w-16 h-16 rounded-2xl flex items-center justify-center text-3xl flex-shrink-0"
              style={{ background: room.color + '33' }}
            >
              {room.icon}
            </div>

            <div>
              <h1 className="font-display text-2xl text-forest-500">{room.name}</h1>
              <p className="text-sm text-neutral-500 mt-1">
                Здесь собраны задачи этой комнаты и актуальные советы из базы знаний.
              </p>
            </div>
          </div>
        </div>
      </div>

      <section className="space-y-3">
        <div className="flex items-center gap-2">
          <CheckSquare size={18} className="text-forest-500" />
          <h2 className="font-display text-lg text-neutral-700">Задачи комнаты</h2>
        </div>

        {roomTasks.length === 0 ? (
          <div className="card text-center text-neutral-400 py-10">
            <p className="text-3xl mb-2">🧺</p>
            <p>Для этой комнаты пока нет задач</p>
          </div>
        ) : (
          <div className="space-y-3">
            {roomTasks.map(task => (
              <div key={task.id} className="card">
                <div className="flex items-start justify-between gap-3 mb-3">
                  <div>
                    <h3 className="font-medium text-neutral-800">{task.title}</h3>
                    {task.description && (
                      <p className="text-sm text-neutral-500 mt-1">{task.description}</p>
                    )}
                  </div>

                  <Badge variant={PRIORITY_VARIANTS[task.priority] ?? 'default'}>
                    {PRIORITY_LABELS[task.priority] ?? task.priority}
                  </Badge>
                </div>

                <div className="flex flex-wrap gap-2">
                  <Badge variant="info">
                    {FREQUENCY_LABELS[task.frequency] ?? task.frequency}
                  </Badge>

                  <Badge variant="default">
                    С {new Date(task.start_date).toLocaleDateString('ru-RU')}
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      <section className="space-y-3">
        <div className="flex items-center gap-2">
          <Lightbulb size={18} className="text-forest-500" />
          <h2 className="font-display text-lg text-neutral-700">Актуальные советы</h2>
        </div>

        {adviceLoading ? (
          <div className="flex justify-center py-6">
            <Spinner className="w-6 h-6" />
          </div>
        ) : featuredAdvice.length === 0 ? (
          <div className="card text-center text-neutral-400 py-10">
            <p className="text-3xl mb-2">💡</p>
            <p>Для этой комнаты советы пока не добавлены</p>
          </div>
        ) : (
          <div className="space-y-3">
            {featuredAdvice.map(item => (
              <div key={item.id} className="card">
                <h3 className="font-display text-base text-neutral-800 mb-1">{item.title}</h3>
                <p className="text-sm text-neutral-600">{item.content}</p>

                {item.steps.length > 0 && (
                  <ul className="mt-3 space-y-1">
                    {item.steps.slice(0, 3).map((step, index) => (
                      <li key={index} className="flex gap-2 text-sm text-neutral-700">
                        <span className="text-forest-500 font-semibold">{index + 1}.</span>
                        <span>{step}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            ))}

            <Link
              to={`/knowledge/room/${encodeURIComponent(room.name)}`}
              className="inline-flex items-center gap-2 text-sm font-medium text-forest-500 hover:text-forest-600 transition-colors"
            >
              Смотреть все советы для комнаты
              <ArrowRight size={16} />
            </Link>
          </div>
        )}
      </section>
    </div>
  )
}