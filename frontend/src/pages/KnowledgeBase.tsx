import { useState, useMemo } from 'react'
import { Search, ChevronDown, ChevronUp, Lightbulb } from 'lucide-react'
import { useAdvice } from '../hooks/useAdvice'
import { Badge } from '../components/ui/Badge'
import { Spinner } from '../components/ui/Spinner'
import type { Advice } from '../types'

type SeasonFilter = 'all' | 'spring' | 'summer' | 'autumn' | 'winter'
type CategoryFilter = 'all' | 'regular' | 'deep' | 'prevention' | 'storage' | 'nonobvious'

const SEASON_TABS: { value: SeasonFilter; label: string; emoji: string }[] = [
  { value: 'all',    label: 'Все',    emoji: '' },
  { value: 'spring', label: 'Весна',  emoji: '🌱' },
  { value: 'summer', label: 'Лето',   emoji: '☀️' },
  { value: 'autumn', label: 'Осень',  emoji: '🍂' },
  { value: 'winter', label: 'Зима',   emoji: '❄️' },
]

const CATEGORY_CHIPS: { value: CategoryFilter; label: string; icon?: string }[] = [
  { value: 'all',        label: 'Все' },
  { value: 'regular',    label: 'Регулярный' },
  { value: 'deep',       label: 'Генеральная уборка' },
  { value: 'prevention', label: 'Профилактика' },
  { value: 'storage',    label: 'Хранение' },
  { value: 'nonobvious', label: 'Необычные' },
]

const SEASON_BADGE: Record<string, { label: string; cls: string }> = {
  spring: { label: '🌱 Весна',  cls: 'bg-emerald-100 text-emerald-700' },
  summer: { label: '☀️ Лето',  cls: 'bg-amber-100  text-amber-700'   },
  autumn: { label: '🍂 Осень', cls: 'bg-orange-100 text-orange-700'  },
  winter: { label: '❄️ Зима',  cls: 'bg-blue-100   text-blue-700'    },
}

const CATEGORY_BADGE: Record<string, { label: string; cls: string }> = {
  deep:       { label: 'Глубокая уборка', cls: 'bg-purple-100 text-purple-700' },
  prevention: { label: 'Профилактика',    cls: 'bg-sky-100    text-sky-700'    },
  storage:    { label: 'Хранение',        cls: 'bg-rose-100   text-rose-700'   },
  nonobvious: { label: 'Неочевидный',     cls: 'bg-yellow-100 text-yellow-700' },
}

function SeasonBadge({ season }: { season?: string | null }) {
  if (!season) return null
  const badge = SEASON_BADGE[season]
  if (!badge) return null
  return (
    <span className={`inline-flex items-center text-xs px-2 py-0.5 rounded-full font-medium ${badge.cls}`}>
      {badge.label}
    </span>
  )
}

function CategoryBadge({ category }: { category: string }) {
  const badge = CATEGORY_BADGE[category]
  if (!badge) return null
  return (
    <span className={`inline-flex items-center text-xs px-2 py-0.5 rounded-full font-medium ${badge.cls}`}>
      {badge.label}
    </span>
  )
}

function AdviceCard({ advice, highlight }: { advice: Advice; highlight?: boolean }) {
  const [expanded, setExpanded] = useState(false)
  const hasSteps = advice.steps.length > 0

  return (
    <div className={`card ${highlight ? 'border-l-4 border-l-yellow-400 bg-yellow-50/20' : ''}`}>
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <div className="flex items-start gap-2 mb-1">
            {highlight && <Lightbulb size={15} className="text-yellow-500 flex-shrink-0 mt-0.5" />}
            <h3 className="font-display text-base text-neutral-800 leading-snug">{advice.title}</h3>
          </div>
          <p className="text-sm text-neutral-600">{advice.content}</p>
          <div className="flex flex-wrap gap-1 mt-2">
            {advice.room_names.map(r => (
              <Badge key={r} variant="success">{r}</Badge>
            ))}
            <SeasonBadge season={advice.season} />
            <CategoryBadge category={advice.category} />
          </div>
        </div>
        {hasSteps && (
          <button
            onClick={() => setExpanded(e => !e)}
            className="text-neutral-400 hover:text-forest-500 transition-colors flex-shrink-0 mt-0.5"
            aria-label={expanded ? 'Скрыть шаги' : 'Показать шаги'}
          >
            {expanded ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
          </button>
        )}
      </div>

      {expanded && (
        <div className="mt-3 pt-3 border-t border-beige-200 animate-fade-in">
          <p className="text-xs font-medium text-neutral-500 uppercase tracking-wide mb-2">Шаги</p>
          <ol className="space-y-1">
            {advice.steps.map((step, i) => (
              <li key={i} className="flex gap-2 text-sm text-neutral-700">
                <span className="text-forest-400 font-semibold flex-shrink-0">{i + 1}.</span>
                <span>{step}</span>
              </li>
            ))}
          </ol>
        </div>
      )}
    </div>
  )
}

export default function KnowledgeBase() {
  const [search, setSearch]     = useState('')
  const [season, setSeason]     = useState<SeasonFilter>('all')
  const [category, setCategory] = useState<CategoryFilter>('all')
  const { data: advice = [], isLoading } = useAdvice()

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase()
    return advice.filter(a => {
      if (season !== 'all' && a.season !== season) return false
      if (category !== 'all' && a.category !== category) return false
      if (q &&
        !a.title.toLowerCase().includes(q) &&
        !a.content.toLowerCase().includes(q) &&
        !a.room_names.some(r => r.toLowerCase().includes(q))) return false
      return true
    })
  }, [advice, search, season, category])

  const isDefaultView = season === 'all' && category === 'all' && !search.trim()

  const { roomGroups, nonObvious } = useMemo(() => {
    if (!isDefaultView) return { roomGroups: null, nonObvious: [] as Advice[] }
    const no   = filtered.filter(a => a.category === 'nonobvious')
    const rest = filtered.filter(a => a.category !== 'nonobvious')
    const map  = new Map<string, Advice[]>()
    rest.forEach(a => {
      const rooms = a.room_names.length > 0 ? a.room_names : ['Общее']
      rooms.forEach(r => {
        if (!map.has(r)) map.set(r, [])
        if (!map.get(r)!.find(x => x.id === a.id)) map.get(r)!.push(a)
      })
    })
    return { roomGroups: map, nonObvious: no }
  }, [filtered, isDefaultView])

  return (
    <div className="space-y-5 max-w-3xl mx-auto">
      {/* Header */}
      <div>
        <h1 className="font-display text-2xl text-forest-500">База знаний</h1>
        {!isLoading && (
          <p className="text-sm text-neutral-500 mt-0.5">{advice.length} советов в базе</p>
        )}
      </div>

      {/* Season tabs */}
      <div className="flex gap-1.5 overflow-x-auto pb-1 -mx-1 px-1">
        {SEASON_TABS.map(tab => (
          <button
            key={tab.value}
            onClick={() => setSeason(tab.value)}
            className={`flex-shrink-0 px-3.5 py-1.5 rounded-full text-sm font-medium transition-colors whitespace-nowrap
              ${season === tab.value
                ? 'bg-forest-500 text-white'
                : 'bg-beige-100 text-neutral-600 hover:bg-beige-200'
              }`}
          >
            {tab.emoji && <span className="mr-1">{tab.emoji}</span>}
            {tab.label}
          </button>
        ))}
      </div>

      {/* Category chips */}
      <div className="flex flex-wrap gap-1.5">
        {CATEGORY_CHIPS.map(chip => (
          <button
            key={chip.value}
            onClick={() => setCategory(chip.value)}
            className={`px-3 py-1 rounded-full text-xs font-medium transition-colors
              ${category === chip.value
                ? 'bg-forest-500 text-white'
                : 'bg-beige-100 text-neutral-600 hover:bg-beige-200'
              }`}
          >
            {chip.icon && <span className="mr-1">{chip.icon}</span>}
            {chip.label}
          </button>
        ))}
      </div>

      {/* Search */}
      <div className="relative">
        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-neutral-400" />
        <input
          className="input pl-9"
          placeholder="Поиск советов..."
          value={search}
          onChange={e => setSearch(e.target.value)}
        />
      </div>

      {/* Content */}
      {isLoading ? (
        <div className="flex justify-center py-12">
          <Spinner className="w-8 h-8" />
        </div>

      ) : filtered.length === 0 ? (
        <div className="card text-center text-neutral-400 py-10">
          <p className="text-3xl mb-2">📚</p>
          <p>Советов не найдено</p>
        </div>

      ) : !isDefaultView ? (
        /* Flat filtered list */
        <div className="space-y-3">
          <p className="text-xs text-neutral-400">{filtered.length} советов по фильтрам</p>
          {filtered.map(a => (
            <AdviceCard key={a.id} advice={a} highlight={a.category === 'nonobvious'} />
          ))}
        </div>

      ) : (
        /* Default grouped view */
        <div className="space-y-8">
          {roomGroups && Array.from(roomGroups.entries()).map(([room, items]) => (
            <section key={room} className="space-y-3">
              <h2 className="font-display text-lg text-neutral-700 border-b border-beige-200 pb-1.5">
                {room}
              </h2>
              <div className="space-y-3">
                {items.map(a => <AdviceCard key={a.id} advice={a} />)}
              </div>
            </section>
          ))}

          {nonObvious.length > 0 && (
            <section className="space-y-3">
              <div className="flex items-center gap-2 border-b border-yellow-200 pb-1.5">
                <Lightbulb size={18} className="text-yellow-500" />
                <h2 className="font-display text-lg text-neutral-700">Неочевидные советы</h2>
                <span className="text-xs text-neutral-400 ml-auto">{nonObvious.length} советов</span>
              </div>
              <div className="space-y-3">
                {nonObvious.map(a => <AdviceCard key={a.id} advice={a} highlight />)}
              </div>
            </section>
          )}
        </div>
      )}
    </div>
  )
}
