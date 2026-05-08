import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { Bell, BellOff, BellRing } from 'lucide-react'
import { authApi } from '../api/auth'
import { useAuthStore } from '../store/authStore'
import { usePushNotifications } from '../hooks/usePushNotifications'
import type { User } from '../types'

export default function Profile() {
  const { updateUserData } = useAuthStore()
  const push = usePushNotifications()

  const [loading, setLoading] = useState(true)
  const [savingProfile, setSavingProfile] = useState(false)
  const [savingPassword, setSavingPassword] = useState(false)

  const [profile, setProfile] = useState<User | null>(null)
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [repeatPassword, setRepeatPassword] = useState('')

  useEffect(() => {
    const loadProfile = async () => {
      try {
        const user = await authApi.me()
        setProfile(user)
        setName(user.name ?? '')
        setEmail(user.email ?? '')
        updateUserData(user.name)
      } catch {
        toast.error('Не удалось загрузить профиль')
      } finally {
        setLoading(false)
      }
    }
    loadProfile()
  }, [updateUserData])

  const handleSaveProfile = async () => {
    if (!name.trim() || !email.trim()) {
      toast.error('Имя и email обязательны')
      return
    }
    setSavingProfile(true)
    try {
      const updated = await authApi.updateMe({ name: name.trim(), email: email.trim() })
      setProfile(updated)
      updateUserData(updated.name)
      toast.success('Профиль обновлён')
    } catch (error: any) {
      toast.error(error?.response?.data?.detail || 'Ошибка сохранения профиля')
    } finally {
      setSavingProfile(false)
    }
  }

  const handleChangePassword = async () => {
    if (!currentPassword || !newPassword || !repeatPassword) {
      toast.error('Заполните все поля для смены пароля')
      return
    }
    if (newPassword.length < 6) {
      toast.error('Новый пароль должен быть не короче 6 символов')
      return
    }
    if (newPassword !== repeatPassword) {
      toast.error('Новые пароли не совпадают')
      return
    }
    setSavingPassword(true)
    try {
      await authApi.changePassword(currentPassword, newPassword)
      setCurrentPassword('')
      setNewPassword('')
      setRepeatPassword('')
      toast.success('Пароль успешно изменён')
    } catch (error: any) {
      toast.error(error?.response?.data?.detail || 'Ошибка смены пароля')
    } finally {
      setSavingPassword(false)
    }
  }

  const handlePushToggle = async () => {
    if (push.isSubscribed) {
      const ok = await push.unsubscribe()
      if (ok) toast.success('Уведомления отключены')
    } else {
      const result = await push.subscribe()
      if (result === 'success') {
        toast.success('Уведомления включены')
      } else if (result === 'denied') {
        toast.error('Уведомления заблокированы в настройках браузера')
      }
    }
  }

  if (loading) {
    return (
      <div className="max-w-3xl mx-auto">
        <div className="card">
          <p className="text-neutral-500">Загрузка профиля...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div>
        <h1 className="font-display text-2xl text-forest-500">Профиль</h1>
        <p className="text-sm text-neutral-500 mt-1">
          Управление личными данными и безопасностью аккаунта
        </p>
      </div>

      {/* Avatar card */}
      <div className="card">
        <div className="flex flex-col md:flex-row gap-5 md:items-center">
          <div className="flex-shrink-0">
            <div className="w-24 h-24 rounded-full bg-forest-200 flex items-center justify-center text-forest-600 text-3xl font-semibold">
              {name?.[0] ?? '?'}
            </div>
          </div>
          <div className="flex-1">
            <p className="font-display text-xl text-neutral-800">{profile?.name}</p>
            <p className="text-sm text-neutral-500 mt-1">{profile?.email}</p>
          </div>
        </div>
      </div>

      {/* Personal data */}
      <div className="card space-y-4">
        <div>
          <h2 className="font-display text-lg text-neutral-800">Личные данные</h2>
          <p className="text-sm text-neutral-500 mt-1">Здесь можно изменить имя и email.</p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="label">Имя *</label>
            <input className="input" value={name} onChange={e => setName(e.target.value)} placeholder="Ваше имя" />
          </div>
          <div>
            <label className="label">Email *</label>
            <input className="input" type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="you@example.com" />
          </div>
        </div>
        <div className="pt-2">
          <button className="btn-primary" onClick={handleSaveProfile} disabled={savingProfile}>
            {savingProfile ? 'Сохранение...' : 'Сохранить профиль'}
          </button>
        </div>
      </div>

      {/* Password */}
      <div className="card space-y-4">
        <div>
          <h2 className="font-display text-lg text-neutral-800">Смена пароля</h2>
          <p className="text-sm text-neutral-500 mt-1">
            Для изменения пароля введите текущий пароль и новый.
          </p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="label">Текущий пароль</label>
            <input className="input" type="password" value={currentPassword} onChange={e => setCurrentPassword(e.target.value)} placeholder="••••••••" />
          </div>
          <div>
            <label className="label">Новый пароль</label>
            <input className="input" type="password" value={newPassword} onChange={e => setNewPassword(e.target.value)} placeholder="••••••••" />
          </div>
          <div>
            <label className="label">Повторите пароль</label>
            <input className="input" type="password" value={repeatPassword} onChange={e => setRepeatPassword(e.target.value)} placeholder="••••••••" />
          </div>
        </div>
        <div className="pt-2">
          <button className="btn-primary" onClick={handleChangePassword} disabled={savingPassword}>
            {savingPassword ? 'Обновление...' : 'Изменить пароль'}
          </button>
        </div>
      </div>

      {/* Push notifications */}
      <div className="card space-y-4">
        <div>
          <h2 className="font-display text-lg text-neutral-800">Уведомления</h2>
          <p className="text-sm text-neutral-500 mt-1">
            Получайте напоминания о задачах и новых назначениях.
          </p>
        </div>

        {!push.isSupported ? (
          <div className="flex items-center gap-3 p-3 rounded-lg bg-beige-100 text-sm text-neutral-500">
            <BellOff size={16} />
            <span>Ваш браузер не поддерживает push-уведомления</span>
          </div>
        ) : push.permission === 'denied' ? (
          <div className="flex items-start gap-3 p-3 rounded-lg bg-amber-50 border border-amber-200 text-sm text-amber-800">
            <BellOff size={16} className="mt-0.5 shrink-0" />
            <div>
              <p className="font-medium">Уведомления заблокированы</p>
              <p className="text-amber-700 mt-0.5">
                Разрешите уведомления в настройках браузера для этого сайта.
              </p>
            </div>
          </div>
        ) : (
          <div className="flex items-center justify-between gap-4 p-3 rounded-lg bg-beige-50 border border-beige-200">
            <div className="flex items-center gap-3">
              {push.isSubscribed
                ? <BellRing size={18} className="text-forest-500" />
                : <Bell size={18} className="text-neutral-400" />
              }
              <div>
                <p className="text-sm font-medium text-neutral-800">
                  {push.isSubscribed ? 'Уведомления включены' : 'Уведомления выключены'}
                </p>
                <p className="text-xs text-neutral-500 mt-0.5">
                  {push.isSubscribed
                    ? 'Вы получаете напоминания о задачах и назначениях'
                    : 'Включите, чтобы получать напоминания о предстоящих задачах'
                  }
                </p>
              </div>
            </div>
            <button
              onClick={handlePushToggle}
              disabled={push.isLoading}
              className={`shrink-0 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                push.isSubscribed
                  ? 'bg-neutral-100 text-neutral-600 hover:bg-neutral-200'
                  : 'bg-forest-500 text-white hover:bg-forest-600'
              }`}
            >
              {push.isLoading
                ? '...'
                : push.isSubscribed ? 'Отключить' : 'Включить'}
            </button>
          </div>
        )}

        {push.error && (
          <p className="text-sm text-red-600">{push.error}</p>
        )}
      </div>
    </div>
  )
}
