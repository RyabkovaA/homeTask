import { useState, useMemo } from 'react'
import { Search, ChevronDown, ChevronUp, ArrowRight } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useAdvice } from '../hooks/useAdvice'
import { Badge } from '../components/ui/Badge'
import { Spinner } from '../components/ui/Spinner'
import type { Advice } from '../types'

function AdviceCard({ advice }: { advice: Advice }) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div className="card">
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1">
          <h3 className="font-display text-base text-neutral-800 mb-1">{advice.title}</h3>
          <p className="text-sm text-neutral-600">{advice.content}</p>
          <div className="flex flex-wrap gap-1 mt-2">
            {advice.room_names.map(r => (
              <Badge key={r} variant="success">{r}</Badge>
            ))}
          </div>
        </div>
        <button
          onClick={() => setExpanded(e => !e)}
          className="text-neutral-400 hover:text-forest-500 transition-colors flex-shrink-0"
        >
          {expanded ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
        </button>
      </div>

      {expanded && advice.steps.length > 0 && (
        <div className="mt-3 pt-3 border-t border-beige-200 animate-fade-in">
          <p className="text-xs font-medium text-neutral-500 uppercase tracking-wide mb-2">Шаги</p>
          <ol className="space-y-1">
            {advice.steps.map((step, i) => (
              <li key={i} className="flex gap-2 text-sm text-neutral-700">
                <span className="text-forest-400 font-semibold flex-shrink-0">{i + 1}.</span>
                {step}
              </li>
            ))}
          </ol>
        </div>
      )}
    </div>
  )
}

export default function KnowledgeBase() {
  const [search, setSearch] = useState('')
  const { data: advice = [], isLoading } = useAdvice()

  const grouped = useMemo(() => {
    const normalizedSearch = search.trim().toLowerCase()

    const filtered = advice.filter(a =>
      !normalizedSearch ||
      a.title.toLowerCase().includes(normalizedSearch) ||
      a.content.toLowerCase().includes(normalizedSearch) ||
      a.room_names.some(room => room.toLowerCase().includes(normalizedSearch))
    )

    const map = new Map<string, Advice[]>()

    filtered.forEach(a => {
      const rooms = a.room_names.length > 0 ? a.room_names : ['Общее']
      rooms.forEach(r => {
        if (!map.has(r)) map.set(r, [])
        if (!map.get(r)!.find(x => x.id === a.id)) {
          map.get(r)!.push(a)
        }
      })
    })

    return map
  }, [advice, search])

  return (
    <div className="space-y-6 max-w-3xl mx-auto">
      <div className="flex items-center justify-between gap-3">
        <h1 className="font-display text-2xl text-forest-500">База знаний</h1>
      </div>

      <div className="relative">
        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-neutral-400" />
        <input
          className="input pl-9"
          placeholder="Поиск советов..."
          value={search}
          onChange={e => setSearch(e.target.value)}
        />
      </div>

      {isLoading ? (
        <div className="flex justify-center py-12">
          <Spinner className="w-8 h-8" />
        </div>
      ) : grouped.size === 0 ? (
        <div className="card text-center text-neutral-400 py-10">
          <p className="text-3xl mb-2">📚</p>
          <p>Советов не найдено</p>
        </div>
      ) : (
        Array.from(grouped.entries()).map(([room, items]) => (
          <section key={room} className="space-y-3">
            <div className="flex items-center justify-between gap-3">
              <h2 className="font-display text-lg text-neutral-700">{room}</h2>

              <Link
                to={`/knowledge/room/${encodeURIComponent(room)}`}
                className="inline-flex items-center gap-1.5 text-sm font-medium text-forest-500 hover:text-forest-600 transition-colors"
              >
                Подробнее
                <ArrowRight size={16} />
              </Link>
            </div>

            <div className="space-y-3">
              {items.map(a => <AdviceCard key={a.id} advice={a} />)}
            </div>
          </section>
        ))
      )}
    </div>
  )
}