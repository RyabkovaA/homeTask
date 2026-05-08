import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import { authApi } from '../api/auth'
import { housesApi } from '../api/houses'
import { useAuthStore } from '../store/authStore'
import { Button } from '../components/ui/Button'
import client from '../api/client'

type Tab = 'login' | 'register'
type OnboardingStep = 'choice' | 'create' | 'join'

export default function Login() {
  const [tab, setTab] = useState<Tab>('login')
  const [email, setEmail] = useState('')
  const [name, setName] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)

  // Onboarding state (shown after successful registration)
  const [onboarding, setOnboarding] = useState(false)
  const [onboardingStep, setOnboardingStep] = useState<OnboardingStep>('choice')
  const [houseName, setHouseName] = useState('')
  const [inviteCode, setInviteCode] = useState('')

  const { setAuth } = useAuthStore()
  const navigate = useNavigate()

  const finalizeLogin = async (token: string) => {
    localStorage.setItem('access_token', token)
    const user = await authApi.me()
    let houseId = ''
    let memberId = ''
    try {
      const resp = await client.get<{ house_id: string; member_id: string }>('/auth/member')
      houseId = resp.data.house_id
      memberId = resp.data.member_id
    } catch {
      // no house yet
    }
    if (!houseId) {
      // Show onboarding even for existing accounts without a house
      setAuth(token, '', '', user.name)
      setOnboarding(true)
      setOnboardingStep('choice')
    } else {
      setAuth(token, houseId, memberId, user.name)
      navigate('/')
    }
  }

  const getToken = async (em: string, pw: string): Promise<string> => {
    const { access_token } = await authApi.login(em, pw)
    return access_token
  }

  const handleLogin = async () => {
    if (!email || !password) { toast.error('Заполните все поля'); return }
    setLoading(true)
    try {
      const token = await getToken(email, password)
      await finalizeLogin(token)
    } catch (error: any) {
      if (error?.response?.status === 401) toast.error('Неверный email или пароль')
      else toast.error('Ошибка входа. Проверьте, запущен ли сервер')
    } finally {
      setLoading(false)
    }
  }

  const handleRegister = async () => {
    if (!email || !name || !password) { toast.error('Заполните все поля'); return }
    setLoading(true)
    try {
      await authApi.register(email, name, password)
      // Pre-auth so subsequent house API calls work
      const token = await getToken(email, password)
      localStorage.setItem('access_token', token)
      toast.success('Аккаунт создан!')
      setOnboarding(true)
      setOnboardingStep('choice')
    } catch {
      toast.error('Ошибка регистрации. Email уже занят?')
    } finally {
      setLoading(false)
    }
  }

  const handleCreateHouse = async () => {
    if (!houseName.trim()) { toast.error('Введите название дома'); return }
    setLoading(true)
    try {
      const house = await housesApi.create({ name: houseName.trim() })
      const resp = await client.get<{ house_id: string; member_id: string }>('/auth/member')
      const user = await authApi.me()
      setAuth(localStorage.getItem('access_token')!, house.id, resp.data.member_id, user.name)
      toast.success('Дом создан!')
      navigate('/')
    } catch {
      toast.error('Ошибка создания дома')
    } finally {
      setLoading(false)
    }
  }

  const handleJoinHouse = async () => {
    if (inviteCode.trim().length !== 8) { toast.error('Код приглашения — 8 символов'); return }
    setLoading(true)
    try {
      const house = await housesApi.join(inviteCode.trim())
      const resp = await client.get<{ house_id: string; member_id: string }>('/auth/member')
      const user = await authApi.me()
      setAuth(localStorage.getItem('access_token')!, house.id, resp.data.member_id, user.name)
      toast.success('Вы присоединились к дому!')
      navigate('/')
    } catch (error: any) {
      if (error?.response?.status === 404) toast.error('Неверный код приглашения')
      else if (error?.response?.status === 400) toast.error('Вы уже в этом доме')
      else toast.error('Ошибка при подключении')
    } finally {
      setLoading(false)
    }
  }

  // Onboarding screen
  if (onboarding) {
    return (
      <div className="min-h-screen bg-beige-100 flex items-center justify-center p-4">
        <div className="w-full max-w-sm">
          <div className="text-center mb-8">
            <span className="text-5xl">🏡</span>
            <h1 className="font-display text-3xl text-forest-500 mt-2">HomeTask</h1>
            <p className="text-sm text-neutral-500 mt-1">Добро пожаловать, {name}!</p>
          </div>

          <div className="card space-y-4">
            {onboardingStep === 'choice' && (
              <>
                <h2 className="font-display text-lg text-neutral-700 text-center">Что хотите сделать?</h2>
                <button
                  onClick={() => setOnboardingStep('create')}
                  className="w-full flex items-center gap-4 p-4 rounded-xl border-2 border-beige-200 hover:border-forest-400 hover:bg-forest-50 transition-all text-left"
                >
                  <span className="text-3xl">🏠</span>
                  <div>
                    <p className="font-medium text-neutral-800">Создать дом</p>
                    <p className="text-xs text-neutral-500 mt-0.5">Вы станете администратором и сможете пригласить других</p>
                  </div>
                </button>
                <button
                  onClick={() => setOnboardingStep('join')}
                  className="w-full flex items-center gap-4 p-4 rounded-xl border-2 border-beige-200 hover:border-forest-400 hover:bg-forest-50 transition-all text-left"
                >
                  <span className="text-3xl">🔗</span>
                  <div>
                    <p className="font-medium text-neutral-800">Присоединиться по коду</p>
                    <p className="text-xs text-neutral-500 mt-0.5">Введите код приглашения от администратора дома</p>
                  </div>
                </button>
              </>
            )}

            {onboardingStep === 'create' && (
              <>
                <button onClick={() => setOnboardingStep('choice')} className="text-xs text-neutral-400 hover:text-neutral-600">← Назад</button>
                <h2 className="font-display text-lg text-neutral-700">Создать дом</h2>
                <div>
                  <label className="label">Название дома</label>
                  <input
                    className="input"
                    placeholder="Например: Квартира на Ленина"
                    value={houseName}
                    onChange={e => setHouseName(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && handleCreateHouse()}
                    autoFocus
                  />
                </div>
                <Button className="w-full" onClick={handleCreateHouse} disabled={loading}>
                  {loading ? 'Создаём...' : 'Создать и войти'}
                </Button>
              </>
            )}

            {onboardingStep === 'join' && (
              <>
                <button onClick={() => setOnboardingStep('choice')} className="text-xs text-neutral-400 hover:text-neutral-600">← Назад</button>
                <h2 className="font-display text-lg text-neutral-700">Присоединиться</h2>
                <div>
                  <label className="label">Код приглашения</label>
                  <input
                    className="input uppercase tracking-widest font-mono"
                    placeholder="A1B2C3D4"
                    maxLength={8}
                    value={inviteCode}
                    onChange={e => setInviteCode(e.target.value.toUpperCase())}
                    onKeyDown={e => e.key === 'Enter' && handleJoinHouse()}
                    autoFocus
                  />
                  <p className="text-xs text-neutral-400 mt-1">8 символов — попросите код у администратора</p>
                </div>
                <Button className="w-full" onClick={handleJoinHouse} disabled={loading}>
                  {loading ? 'Подключаемся...' : 'Войти в дом'}
                </Button>
              </>
            )}
          </div>
        </div>
      </div>
    )
  }

  // Normal login/register screen
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
        </div>
      </div>
    </div>
  )
}
