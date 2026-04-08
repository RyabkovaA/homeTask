import { useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ChevronDown, ChevronUp, ArrowLeft } from 'lucide-react'
import { useAdvice } from '../hooks/useAdvice'
import { Badge } from '../components/ui/Badge'
import { Spinner } from '../components/ui/Spinner'
import type { Advice } from '../types'

function RoomAdviceCard({ advice }: { advice: Advice }) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div className="card">
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1">
          <h3 className="font-display text-lg text-neutral-800 mb-1">{advice.title}</h3>
          <p className="text-sm text-neutral-600">{advice.content}</p>

          <div className="flex flex-wrap gap-1 mt-3">
            {advice.room_names.map(room => (
              <Badge key={room} variant="success">{room}</Badge>
            ))}
          </div>
        </div>

        <button
          onClick={() => setExpanded(v => !v)}
          className="text-neutral-400 hover:text-forest-500 transition-colors flex-shrink-0"
        >
          {expanded ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
        </button>
      </div>

      {expanded && advice.steps.length > 0 && (
        <div className="mt-4 pt-4 border-t border-beige-200 animate-fade-in">
          <p className="text-xs font-medium text-neutral-500 uppercase tracking-wide mb-3">
            Пошаговая инструкция
          </p>
          <ol className="space-y-2">
            {advice.steps.map((step, index) => (
              <li key={index} className="flex gap-3 text-sm text-neutral-700">
                <span className="text-forest-500 font-semibold flex-shrink-0">{index + 1}.</span>
                <span>{step}</span>
              </li>
            ))}
          </ol>
        </div>
      )}
    </div>
  )
}

function getRoomGeneratedTips(roomName: string) {
  const normalized = roomName.toLowerCase()

  if (normalized.includes('кух')) {
    return [
      'Проветривайте кухню после готовки, чтобы снизить влажность и запахи.',
      'Раз в неделю протирайте фасады и ручки шкафов — там быстро накапливается жир.',
      'Держите мойку пустой перед сном, чтобы утро начиналось с визуального порядка.'
    ]
  }

  if (normalized.includes('ван')) {
    return [
      'После душа оставляйте дверь приоткрытой для снижения риска плесени.',
      'Раз в несколько дней быстро протирайте смесители, чтобы не копился налёт.',
      'Храните базовые чистящие средства в одной корзине — так уборка занимает меньше времени.'
    ]
  }

  if (normalized.includes('спаль')) {
    return [
      'Проветривайте комнату утром 10–15 минут для более комфортного микроклимата.',
      'Используйте одну корзину или зону для вещей, которые пока не разобраны.',
      'Смена постельного белья по расписанию заметно повышает ощущение уюта.'
    ]
  }

  if (normalized.includes('гостин')) {
    return [
      'Разделите уборку на короткие циклы: поверхности, мягкая мебель, пол.',
      'Храните мелкие вещи в одной декоративной корзине, чтобы визуально разгрузить комнату.',
      'Быстрый вечерний сброс вещей по местам помогает не накапливать хаос.'
    ]
  }

  if (normalized.includes('балкон')) {
    return [
      'Проверяйте балкон раз в несколько дней на пыль и лишние предметы.',
      'Для растений удобно объединять полив и быстрый визуальный осмотр в один ритуал.',
      'Сезонное расхламление балкона лучше планировать отдельной задачей.'
    ]
  }

  return [
    'Разделите поддержание порядка на короткие регулярные действия.',
    'Храните вещи по категориям, чтобы уменьшить визуальный шум.',
    'Добавьте одну-две повторяющиеся задачи для этой комнаты, чтобы порядок держался автоматически.'
  ]
}

export default function KnowledgeRoom() {
  const { roomName = '' } = useParams()
  const decodedRoomName = decodeURIComponent(roomName)
  const { data: advice = [], isLoading } = useAdvice()

  const roomAdvice = useMemo(
    () =>
      advice.filter(item =>
        item.room_names.some(room => room.toLowerCase() === decodedRoomName.toLowerCase())
      ),
    [advice, decodedRoomName]
  )

  const generatedTips = useMemo(
    () => getRoomGeneratedTips(decodedRoomName),
    [decodedRoomName]
  )

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <Spinner className="w-8 h-8" />
      </div>
    )
  }

  return (
    <div className="space-y-6 max-w-3xl mx-auto">
      <div className="space-y-3">
        <Link
          to="/knowledge"
          className="inline-flex items-center gap-2 text-sm font-medium text-neutral-500 hover:text-forest-500 transition-colors"
        >
          <ArrowLeft size={16} />
          Назад к базе знаний
        </Link>

        <div>
          <h1 className="font-display text-2xl text-forest-500">
            База знаний: {decodedRoomName}
          </h1>
          <p className="text-sm text-neutral-500 mt-1">
            Советы и рекомендации по поддержанию порядка в этой комнате
          </p>
        </div>
      </div>

      <div className="card">
        <h2 className="font-display text-lg text-neutral-800 mb-3">
          Полезные рекомендации для комнаты
        </h2>
        <ul className="space-y-2">
          {generatedTips.map((tip, index) => (
            <li key={index} className="flex gap-3 text-sm text-neutral-700">
              <span className="text-forest-500">•</span>
              <span>{tip}</span>
            </li>
          ))}
        </ul>
      </div>

      <div className="space-y-3">
        <h2 className="font-display text-lg text-neutral-700">
          Советы из базы знаний
        </h2>

        {roomAdvice.length === 0 ? (
          <div className="card text-center text-neutral-400 py-10">
            <p className="text-3xl mb-2">🧺</p>
            <p>Для этой комнаты советы пока не добавлены</p>
          </div>
        ) : (
          roomAdvice.map(item => (
            <RoomAdviceCard key={item.id} advice={item} />
          ))
        )}
      </div>
    </div>
  )
}