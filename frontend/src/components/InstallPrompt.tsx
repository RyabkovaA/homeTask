import { useState, useEffect } from 'react'
import { Download, X } from 'lucide-react'

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>
}

export default function InstallPrompt() {
  const [deferredPrompt, setDeferredPrompt] = useState<BeforeInstallPromptEvent | null>(null)
  const [dismissed, setDismissed] = useState(() =>
    localStorage.getItem('pwa-install-dismissed') === '1'
  )

  useEffect(() => {
    const handler = (e: Event) => {
      e.preventDefault()
      setDeferredPrompt(e as BeforeInstallPromptEvent)
    }
    window.addEventListener('beforeinstallprompt', handler)
    return () => window.removeEventListener('beforeinstallprompt', handler)
  }, [])

  if (!deferredPrompt || dismissed) return null

  const handleInstall = async () => {
    await deferredPrompt.prompt()
    const { outcome } = await deferredPrompt.userChoice
    if (outcome === 'accepted') setDeferredPrompt(null)
  }

  const handleDismiss = () => {
    setDismissed(true)
    localStorage.setItem('pwa-install-dismissed', '1')
  }

  return (
    <div className="fixed bottom-20 left-1/2 -translate-x-1/2 z-50 flex items-center gap-3 px-4 py-3 rounded-xl shadow-lg bg-forest-600 text-white text-sm max-w-xs w-full mx-4">
      <Download size={16} className="shrink-0" />
      <div className="flex-1 min-w-0">
        <p className="font-medium">Установить HomeTask</p>
        <p className="text-forest-100 text-xs mt-0.5">Работайте offline без браузера</p>
      </div>
      <button
        onClick={handleInstall}
        className="shrink-0 px-3 py-1 rounded-lg text-xs font-semibold hover:opacity-90 transition-opacity"
        style={{ background: '#fff', color: '#2D5A3D' }}
      >
        Установить
      </button>
      <button onClick={handleDismiss} className="shrink-0 text-forest-200 hover:text-white">
        <X size={15} />
      </button>
    </div>
  )
}
