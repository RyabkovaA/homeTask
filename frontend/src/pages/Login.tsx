import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import { authApi } from '../api/auth'
import { useAuthStore } from '../store/authStore'
import { Button } from '../components/ui/Button'
import client from '../api/client'

type Tab = 'login' | 'register'

export default function Login() {
  const [tab, setTab] = useState<Tab>('login')
  const [email, setEmail] = useState('')
  const [name, setName] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const { setAuth } = useAuthStore()
  const navigate = useNavigate()

  const doLogin = async (em: string, pw: string) => {
    const { access_token } = await authApi.login(em, pw)
    localStorage.setItem('access_token', access_token)

    const user = await authApi.me()

    let houseId = ''
    let memberId = ''
    try {
      const resp = await client.get<{ house_id: string; member_id: string }>('/auth/member')
      houseId = resp.data.house_id
      memberId = resp.data.member_id
    } catch {
      // пользователь может пока не состоять ни в одном доме
    }

    setAuth(access_token, houseId, memberId, user.name)
    navigate('/')
  }

  const handleLogin = async () => {
    if (!email || !password) {
      toast.error('Заполните все поля')
      return
    }

    setLoading(true)
    try {
      await doLogin(email, password)
    } catch (error: any) {
      if (error?.response?.status === 401) {
        toast.error('Неверный email или пароль')
      } else if (error?.response?.status === 422) {
        toast.error('Ошибка формата запроса при логине')
      } else {
        toast.error('Ошибка входа. Проверьте, запущен ли сервер')
      }
    } finally {
      setLoading(false)
    }
  }

  const handleRegister = async () => {
    if (!email || !name || !password) {
      toast.error('Заполните все поля')
      return
    }

    setLoading(true)
    try {
      await authApi.register(email, name, password)
      toast.success('Аккаунт создан!')
      await doLogin(email, password)
    } catch {
      toast.error('Ошибка регистрации. Email уже занят?')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-beige-100 flex items-center justify-center p-4">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <span className="text-5xl">🏡</span>
          <h1 className="font-display text-3xl text-forest-500 mt-2">HomeTask</h1>
          <p className="text-sm text-neutral-500 mt-1">Управление бытовыми задачами</p>
        </div>

        <div className="card">
          <div className="flex rounded-xl bg-beige-200 p-1 mb-6">
            {(['login', 'register'] as Tab[]).map(t => (
              <button
                key={t}
                onClick={() => setTab(t)}
                className={`flex-1 py-2 rounded-lg text-sm font-medium transition-all ${
                  tab === t ? 'bg-white shadow-sm text-forest-600' : 'text-neutral-500 hover:text-neutral-700'
                }`}
              >
                {t === 'login' ? 'Войти' : 'Зарегистрироваться'}
              </button>
            ))}
          </div>

          <div className="space-y-4">
            <div>
              <label className="label">Email</label>
              <input
                className="input"
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={e => setEmail(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && (tab === 'login' ? handleLogin() : handleRegister())}
              />
            </div>

            {tab === 'register' && (
              <div>
                <label className="label">Имя</label>
                <input
                  className="input"
                  placeholder="Ваше имя"
                  value={name}
                  onChange={e => setName(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && handleRegister()}
                />
              </div>
            )}

            <div>
              <label className="label">Пароль</label>
              <input
                className="input"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={e => setPassword(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && (tab === 'login' ? handleLogin() : handleRegister())}
              />
            </div>

            <Button
              className="w-full"
              onClick={tab === 'login' ? handleLogin : handleRegister}
              disabled={loading}
            >
              {loading ? 'Загрузка...' : tab === 'login' ? 'Войти' : 'Создать аккаунт'}
            </Button>
          </div>

          {/* {tab === 'login' && (
            <p className="text-xs text-neutral-400 text-center mt-4">
              Тест: a@home.ru / password123
            </p>
          )} */}
        </div>
      </div>
    </div>
  )
}