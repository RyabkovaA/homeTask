import { WifiOff, RefreshCw } from 'lucide-react'
import { useOnline } from '../hooks/useOnline'
import { useOfflineStore } from '../store/offlineStore'

interface Props {
  onSync?: () => void
}

export default function OfflineBanner({ onSync }: Props) {
  const isOnline = useOnline()
  const { pendingCount, isSyncing } = useOfflineStore()

  if (isOnline && pendingCount === 0) return null

  return (
    <div
      className={`fixed bottom-4 left-1/2 -translate-x-1/2 z-50 flex items-center gap-2.5 px-4 py-2.5 rounded-xl shadow-lg text-sm font-medium transition-all ${
        isOnline
          ? 'bg-amber-50 text-amber-800 border border-amber-200'
          : 'bg-neutral-800 text-white'
      }`}
    >
      {!isOnline && <WifiOff size={15} className="shrink-0" />}
      {!isOnline && <span>Нет соединения — действия сохраняются локально</span>}
      {isOnline && pendingCount > 0 && (
        <>
          <RefreshCw size={15} className={`shrink-0 ${isSyncing ? 'animate-spin' : ''}`} />
          <span>
            {isSyncing
              ? 'Синхронизация...'
              : `${pendingCount} ${pendingCount === 1 ? 'событие' : 'событий'} ожидают синхронизации`}
          </span>
          {!isSyncing && onSync && (
            <button
              onClick={onSync}
              className="ml-1 underline underline-offset-2 hover:no-underline"
            >
              Синхронизировать
            </button>
          )}
        </>
      )}
    </div>
  )
}
