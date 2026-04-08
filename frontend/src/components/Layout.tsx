import { NavLink, Outlet } from 'react-router-dom'
import { Home, CheckSquare, BarChart2, Building2, BookOpen, LogOut } from 'lucide-react'
import { useAuthStore } from '../store/authStore'
import toast from 'react-hot-toast'

const NAV = [
  { to: '/',          icon: Home,        label: 'Главная'     },
  { to: '/tasks',     icon: CheckSquare, label: 'Задачи'      },
  { to: '/analytics', icon: BarChart2,   label: 'Аналитика'   },
  { to: '/house',     icon: Building2,   label: 'Дом'         },
  { to: '/knowledge', icon: BookOpen,    label: 'База знаний' },
]

export default function Layout() {
  const { userName, logout } = useAuthStore()

  return (
    <div className="flex min-h-screen bg-beige-100">
      {/* Sidebar desktop */}
      <aside className="hidden md:flex flex-col w-60 bg-beige-50 border-r border-beige-200 fixed inset-y-0 z-20">
        <div className="px-6 py-6 border-b border-beige-200">
          <div className="flex items-center gap-2.5">
            <span className="text-2xl">🏡</span>
            <span className="font-display text-xl text-forest-500 font-semibold">HomeTask</span>
          </div>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-1">
          {NAV.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm font-medium transition-all duration-150 ${
                  isActive
                    ? 'bg-forest-400 text-white shadow-sm'
                    : 'text-neutral-600 hover:bg-beige-200 hover:text-forest-500'
                }`
              }
            >
              <Icon size={18} />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="px-4 py-4 border-t border-beige-200">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-forest-200 flex items-center justify-center text-forest-600 font-semibold text-sm">
              {userName?.[0] ?? '?'}
            </div>
            <span className="text-sm font-medium text-neutral-700 flex-1 truncate">{userName}</span>
            <button
              onClick={() => { logout(); toast.success('До свидания!') }}
              className="text-neutral-400 hover:text-forest-500 transition-colors"
            >
              <LogOut size={16} />
            </button>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 md:ml-60 flex flex-col min-h-screen">
        <div className="flex-1 px-4 md:px-8 py-6 animate-fade-in pb-20 md:pb-6">
          <Outlet />
        </div>

        {/* Mobile bottom nav */}
        <nav className="md:hidden fixed bottom-0 inset-x-0 bg-beige-50 border-t border-beige-200 flex justify-around py-2 z-20">
          {NAV.slice(0, 4).map(({ to, icon: Icon, label }) => (
            <NavLink key={to} to={to} end={to === '/'} className={({ isActive }) =>
              `flex flex-col items-center gap-0.5 px-3 py-1 rounded-lg text-xs transition-colors ${
                isActive ? 'text-forest-400 font-semibold' : 'text-neutral-400'
              }`
            }>
              <Icon size={20} />
              {label}
            </NavLink>
          ))}
        </nav>
      </main>
    </div>
  )
}
