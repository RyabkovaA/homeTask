import { useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider, useQueryClient } from '@tanstack/react-query'
import { Toaster } from 'react-hot-toast'
import toast from 'react-hot-toast'
import { useRegisterSW } from 'virtual:pwa-register/react'
import { useAuthStore } from './store/authStore'
import { useOfflineStore } from './store/offlineStore'
import { getPendingEvents, removeEvent } from './utils/offlineQueue'
import { eventsApi } from './api/events'
import Layout from './components/Layout'
import OfflineBanner from './components/OfflineBanner'
import InstallPrompt from './components/InstallPrompt'
import Dashboard from './pages/Dashboard'
import Tasks from './pages/Tasks'
import Analytics from './pages/Analytics'
import House from './pages/House'
import HouseRoom from './pages/HouseRoom'
import KnowledgeBase from './pages/KnowledgeBase'
import KnowledgeRoom from './pages/KnowledgeRoom'
import History from './pages/History'
import Profile from './pages/Profile.tsx'
import Admin from './pages/Admin'
import Login from './pages/Login'
import type { ReactNode } from 'react'

const qc = new QueryClient({
  defaultOptions: { queries: { staleTime: 30_000, retry: 1 } }
})

function ProtectedRoute({ children }: { children: ReactNode }) {
  const { token } = useAuthStore()
  return token ? <>{children}</> : <Navigate to="/login" replace />
}

function SyncManager() {
  const { token } = useAuthStore()
  const queryClient = useQueryClient()
  const { setPendingCount, setIsSyncing } = useOfflineStore()

  // Refresh pending count on mount
  useEffect(() => {
    if (!token) return
    getPendingEvents().then(q => setPendingCount(q.length))
  }, [setPendingCount])

  const flush = async () => {
    const pending = await getPendingEvents()
    if (!pending.length) return

    setIsSyncing(true)
    let synced = 0
    for (const item of pending) {
      try {
        await eventsApi.createDirect(item.payload)
        await removeEvent(item.localId)
        synced++
      } catch {
        // leave in queue, retry next time
      }
    }
    setIsSyncing(false)
    const remaining = await getPendingEvents()
    setPendingCount(remaining.length)
    if (synced > 0) {
      toast.success(`Синхронизировано ${synced} событий`)
      queryClient.invalidateQueries({ queryKey: ['events'] })
      queryClient.invalidateQueries({ queryKey: ['tasks'] })
    }
  }

  // Auto-flush on reconnect
  useEffect(() => {
    const handler = () => {
      getPendingEvents().then(q => {
        if (q.length > 0) flush()
      })
    }
    window.addEventListener('online', handler)
    return () => window.removeEventListener('online', handler)
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  return <OfflineBanner onSync={flush} />
}

function PWAUpdater() {
  useRegisterSW({
    onNeedRefresh() {
      toast('Доступна новая версия приложения. Обновите страницу.', { duration: 8000 })
    },
    onOfflineReady() {
      toast.success('Приложение готово к работе офлайн')
    },
  })
  return null
}

export default function App() {
  return (
    <QueryClientProvider client={qc}>
      <BrowserRouter>
        <Toaster
          position="top-right"
          toastOptions={{
            style: { background: '#FDFAF4', border: '1px solid #EDE5D5', fontFamily: 'DM Sans' }
          }}
        />
        <PWAUpdater />
        <InstallPrompt />
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route element={<ProtectedRoute><Layout /></ProtectedRoute>}>
            <Route index element={<Dashboard />} />
            <Route path="tasks" element={<Tasks />} />
            <Route path="history" element={<History />} />
            <Route path="analytics" element={<Analytics />} />
            <Route path="house" element={<House />} />
            <Route path="house/room/:roomId" element={<HouseRoom />} />
            <Route path="knowledge" element={<KnowledgeBase />} />
            <Route path="knowledge/room/:roomName" element={<KnowledgeRoom />} />
            <Route path="profile" element={<Profile />} />
            <Route path="admin" element={<Admin />} />
          </Route>
        </Routes>
        <ProtectedRoute>
          <SyncManager />
        </ProtectedRoute>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
