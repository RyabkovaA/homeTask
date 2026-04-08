import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'react-hot-toast'
import { useAuthStore } from './store/authStore'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Tasks from './pages/Tasks'
import Analytics from './pages/Analytics'
import House from './pages/House'
import HouseRoom from './pages/HouseRoom'
import KnowledgeBase from './pages/KnowledgeBase'
import KnowledgeRoom from './pages/KnowledgeRoom'
import Profile from './pages/Profile.tsx'
import Login from './pages/Login'
import type { ReactNode } from 'react'

const qc = new QueryClient({
  defaultOptions: { queries: { staleTime: 30_000, retry: 1 } }
})

function ProtectedRoute({ children }: { children: ReactNode }) {
  const { token } = useAuthStore()
  return token ? <>{children}</> : <Navigate to="/login" replace />
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
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route element={<ProtectedRoute><Layout /></ProtectedRoute>}>
            <Route index element={<Dashboard />} />
            <Route path="tasks" element={<Tasks />} />
            <Route path="analytics" element={<Analytics />} />
            <Route path="house" element={<House />} />
            <Route path="house/room/:roomId" element={<HouseRoom />} />
            <Route path="knowledge" element={<KnowledgeBase />} />
            <Route path="knowledge/room/:roomName" element={<KnowledgeRoom />} />
            <Route path="profile" element={<Profile />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}