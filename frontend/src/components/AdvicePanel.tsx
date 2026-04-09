/**
 * AdvicePanel — displays a RAG-generated advice result.
 *
 * Shows:
 *   - main advice text (from top retrieved knowledge fragment)
 *   - step-by-step execution list
 *   - warnings (priority-based, history-based)
 *   - source attribution (which knowledge base items were retrieved)
 *   - traceability: query used, delivery ID
 */
import { useState } from 'react'
import { Lightbulb, ChevronDown, ChevronUp, BookOpen, AlertTriangle, Info } from 'lucide-react'
import type { RagAdvice } from '../types'
import { Badge } from './ui/Badge'
import { Spinner } from './ui/Spinner'

interface AdvicePanelProps {
  advice: RagAdvice | null
  isLoading?: boolean
  error?: boolean
  compact?: boolean
}

export function AdvicePanel({ advice, isLoading, error, compact = false }: AdvicePanelProps) {
  const [showSteps, setShowSteps] = useState(!compact)
  const [showSources, setShowSources] = useState(false)

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 py-3 text-sm text-neutral-500">
        <Spinner className="w-4 h-4" />
        <span>Подбираем совет из базы знаний...</span>
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-sm text-red-500 py-2">
        Не удалось загрузить совет. Попробуйте позже.
      </div>
    )
  }

  if (!advice) return null

  return (
    <div className="mt-3 rounded-xl border border-forest-200 bg-forest-50/60 p-3 space-y-2 animate-fade-in">
      {/* Header */}
      <div className="flex items-center gap-1.5">
        <Lightbulb size={14} className="text-forest-500 flex-shrink-0" />
        <span className="text-xs font-semibold text-forest-600 uppercase tracking-wide">
          Совет из базы знаний
        </span>
      </div>

      {/* Main advice */}
      <p className="text-sm text-neutral-700 leading-relaxed">{advice.main_advice}</p>

      {/* Warnings */}
      {advice.warnings.length > 0 && (
        <div className="space-y-1">
          {advice.warnings.map((w, i) => (
            <div key={i} className="flex gap-1.5 text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-2.5 py-1.5">
              <AlertTriangle size={12} className="flex-shrink-0 mt-0.5" />
              <span>{w}</span>
            </div>
          ))}
        </div>
      )}

      {/* Steps toggle */}
      {advice.steps.length > 0 && (
        <div>
          <button
            onClick={() => setShowSteps(s => !s)}
            className="flex items-center gap-1 text-xs font-medium text-forest-600 hover:text-forest-700 transition-colors"
          >
            {showSteps ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
            {showSteps ? 'Скрыть шаги' : `Показать шаги (${advice.steps.length})`}
          </button>
          {showSteps && (
            <ol className="mt-2 space-y-1">
              {advice.steps.map((step, i) => (
                <li key={i} className="flex gap-2 text-xs text-neutral-700">
                  <span className="text-forest-400 font-bold flex-shrink-0 w-4">{i + 1}.</span>
                  <span>{step}</span>
                </li>
              ))}
            </ol>
          )}
        </div>
      )}

      {/* Sources + traceability */}
      {advice.sources.length > 0 && (
        <div>
          <button
            onClick={() => setShowSources(s => !s)}
            className="flex items-center gap-1 text-xs text-neutral-400 hover:text-neutral-600 transition-colors"
          >
            <BookOpen size={11} />
            {showSources ? 'Скрыть источники' : `Источники (${advice.sources.length})`}
            {showSources ? <ChevronUp size={11} /> : <ChevronDown size={11} />}
          </button>
          {showSources && (
            <div className="mt-1.5 space-y-1">
              {advice.sources.map(src => (
                <div key={src.id} className="flex items-center gap-1.5 text-xs text-neutral-500">
                  <Info size={10} className="flex-shrink-0" />
                  <span className="flex-1">{src.title}</span>
                  <Badge variant="default" className="text-[10px]">
                    {(src.score * 100).toFixed(0)}%
                  </Badge>
                </div>
              ))}
              {advice.history && (
                <div className="pt-1 border-t border-forest-200 text-[11px] text-neutral-400">
                  История (30 дн.): выполнено {advice.history.done}/{advice.history.total}
                  {' '}({advice.history.completion_rate}%)
                  {advice.history.overdue > 0 && `, просрочено ${advice.history.overdue}`}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
