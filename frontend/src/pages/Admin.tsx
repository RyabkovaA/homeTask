import { useState, useMemo } from 'react'
import { Plus, Pencil, Trash2, Check, X, ShieldAlert } from 'lucide-react'
import { useMembers, useInviteMember, useUpdateMember, useRemoveMember } from '../hooks/useMembers'
import { useRooms } from '../hooks/useRooms'
import { useAuthStore } from '../store/authStore'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { housesApi } from '../api/houses'
import { roomsApi } from '../api/rooms'
import { adviceApi } from '../api/advice'
import { Spinner } from '../components/ui/Spinner'
import type { MemberRole, Advice } from '../types'
import toast from 'react-hot-toast'

type Tab = 'house' | 'rooms' | 'members' | 'knowledge'

const ROLE_LABELS: Record<MemberRole, string> = { admin: 'Администратор', member: 'Участник', limited: 'Ограниченный' }
const CATEGORY_OPTIONS = [
  { value: 'regular', label: 'Регулярная' },
  { value: 'deep', label: 'Генеральная' },
  { value: 'prevention', label: 'Профилактика' },
  { value: 'storage', label: 'Хранение' },
  { value: 'nonobvious', label: 'Неочевидный' },
]
const SEASON_OPTIONS = [
  { value: '', label: 'Все сезоны' },
  { value: 'spring', label: 'Весна' },
  { value: 'summer', label: 'Лето' },
  { value: 'autumn', label: 'Осень' },
  { value: 'winter', label: 'Зима' },
]

function AdminGuard({ isAdmin, children }: { isAdmin: boolean; children: React.ReactNode }) {
  if (!isAdmin) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center">
        <ShieldAlert size={48} className="text-red-400 mb-4" />
        <p className="text-lg font-medium text-neutral-700">Доступ запрещён</p>
        <p className="text-sm text-neutral-400 mt-1">Эта страница доступна только администраторам дома</p>
      </div>
    )
  }
  return <>{children}</>
}

// ---- House Tab ----
function HouseTab() {
  const houseId = useAuthStore(s => s.houseId)!
  const qc = useQueryClient()
  const { data: house, isLoading } = useQuery({ queryKey: ['house', houseId], queryFn: () => housesApi.get(houseId) })
  const [name, setName] = useState('')
  const [editing, setEditing] = useState(false)

  const update = useMutation({
    mutationFn: (n: string) => housesApi.update(houseId, { name: n }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['house', houseId] }); setEditing(false); toast.success('Название обновлено') },
    onError: () => toast.error('Ошибка обновления'),
  })

  if (isLoading) return <div className="flex justify-center py-10"><Spinner className="w-6 h-6" /></div>

  return (
    <div className="space-y-4 max-w-md">
      <p className="text-sm text-neutral-500">Управление настройками дома</p>
      {editing ? (
        <div className="flex gap-2">
          <input className="input flex-1" value={name} onChange={e => setName(e.target.value)} placeholder="Название дома" />
          <button onClick={() => update.mutate(name)} disabled={!name.trim() || update.isPending} className="btn-primary px-4 py-2 text-sm">
            {update.isPending ? <Spinner className="w-4 h-4" /> : <Check size={16} />}
          </button>
          <button onClick={() => setEditing(false)} className="btn-secondary px-3 py-2 text-sm"><X size={16} /></button>
        </div>
      ) : (
        <div className="flex items-center gap-3 card">
          <span className="text-2xl">🏡</span>
          <div className="flex-1">
            <p className="font-medium">{house?.name}</p>
            <p className="text-xs text-neutral-400">ID: {houseId.slice(0, 8)}…</p>
          </div>
          <button onClick={() => { setName(house?.name ?? ''); setEditing(true) }} className="text-neutral-400 hover:text-forest-500 transition-colors"><Pencil size={16} /></button>
        </div>
      )}
    </div>
  )
}

// ---- Rooms Tab ----
function RoomsTab() {
  const houseId = useAuthStore(s => s.houseId)!
  const qc = useQueryClient()
  const { data: rooms = [], isLoading } = useRooms()
  const [addName, setAddName] = useState('')
  const [addIcon, setAddIcon] = useState('🛋️')
  const [editId, setEditId] = useState<string | null>(null)
  const [editName, setEditName] = useState('')

  const create = useMutation({
    mutationFn: () => roomsApi.create(houseId, { name: addName, icon: addIcon }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['rooms', houseId] }); setAddName(''); toast.success('Комната добавлена') },
    onError: () => toast.error('Ошибка создания комнаты'),
  })

  const update = useMutation({
    mutationFn: ({ id, name }: { id: string; name: string }) => roomsApi.update(id, { name }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['rooms', houseId] }); setEditId(null); toast.success('Сохранено') },
    onError: () => toast.error('Ошибка'),
  })

  const del = useMutation({
    mutationFn: (id: string) => roomsApi.delete(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['rooms', houseId] }); toast.success('Комната удалена') },
    onError: () => toast.error('Ошибка удаления'),
  })

  if (isLoading) return <div className="flex justify-center py-10"><Spinner className="w-6 h-6" /></div>

  return (
    <div className="space-y-4">
      <div className="flex gap-2 max-w-md">
        <input className="input w-12 text-center text-xl px-1" value={addIcon} onChange={e => setAddIcon(e.target.value)} />
        <input className="input flex-1" placeholder="Название комнаты" value={addName} onChange={e => setAddName(e.target.value)} />
        <button onClick={() => create.mutate()} disabled={!addName.trim() || create.isPending} className="btn-primary px-4 py-2 text-sm">
          <Plus size={16} />
        </button>
      </div>
      <div className="space-y-2 max-w-md">
        {rooms.map(room => (
          <div key={room.id} className="card flex items-center gap-3">
            <span className="text-xl">{room.icon}</span>
            {editId === room.id ? (
              <input className="input flex-1 text-sm" value={editName} onChange={e => setEditName(e.target.value)} />
            ) : (
              <span className="flex-1 text-sm font-medium">{room.name}</span>
            )}
            <div className="flex gap-1">
              {editId === room.id ? (
                <>
                  <button onClick={() => update.mutate({ id: room.id, name: editName })} className="w-7 h-7 rounded-lg bg-forest-100 text-forest-600 flex items-center justify-center"><Check size={13} /></button>
                  <button onClick={() => setEditId(null)} className="w-7 h-7 rounded-lg bg-beige-200 text-neutral-500 flex items-center justify-center"><X size={13} /></button>
                </>
              ) : (
                <>
                  <button onClick={() => { setEditId(room.id); setEditName(room.name) }} className="w-7 h-7 rounded-lg bg-beige-200 text-neutral-500 hover:bg-beige-300 flex items-center justify-center"><Pencil size={13} /></button>
                  <button onClick={() => { if (confirm(`Удалить «${room.name}»?`)) del.mutate(room.id) }} className="w-7 h-7 rounded-lg bg-red-100 text-red-500 hover:bg-red-200 flex items-center justify-center"><Trash2 size={13} /></button>
                </>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

// ---- Members Tab ----
function MembersTab() {
  const houseId = useAuthStore(s => s.houseId)!
  const memberId = useAuthStore(s => s.memberId)!
  const { data: members = [], isLoading } = useMembers()
  const { data: rooms = [] } = useRooms()
  const invite = useInviteMember()
  const updateMember = useUpdateMember()
  const removeMember = useRemoveMember()
  const [email, setEmail] = useState('')
  const [role, setRole] = useState<MemberRole>('member')

  const handleInvite = async () => {
    if (!email.trim()) return
    try {
      await invite.mutateAsync({ email, role })
      setEmail('')
      toast.success('Участник добавлен')
    } catch (e: any) {
      toast.error(e?.response?.data?.detail ?? 'Ошибка приглашения')
    }
  }

  const toggleAllowedRoom = (m: typeof members[number], roomId: string) => {
    const current = m.allowed_room_ids ?? []
    const next = current.includes(roomId)
      ? current.filter(id => id !== roomId)
      : [...current, roomId]
    updateMember.mutate({ memberId: m.id, data: { allowed_room_ids: next } })
  }

  if (isLoading) return <div className="flex justify-center py-10"><Spinner className="w-6 h-6" /></div>

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2 max-w-lg">
        <input className="input flex-1 min-w-48" placeholder="email участника" value={email} onChange={e => setEmail(e.target.value)} />
        <select className="input w-40" value={role} onChange={e => setRole(e.target.value as MemberRole)}>
          {(['member', 'limited', 'admin'] as MemberRole[]).map(r => (
            <option key={r} value={r}>{ROLE_LABELS[r]}</option>
          ))}
        </select>
        <button onClick={handleInvite} disabled={!email.trim() || invite.isPending} className="btn-primary px-4 py-2 text-sm">
          {invite.isPending ? <Spinner className="w-4 h-4" /> : 'Пригласить'}
        </button>
      </div>

      <div className="space-y-2 max-w-lg">
        {members.map(m => (
          <div key={m.id} className="card space-y-2">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-full flex items-center justify-center text-white text-sm font-semibold flex-shrink-0" style={{ background: m.color }}>
                {m.user?.name?.[0] ?? '?'}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{m.user?.name ?? '—'}</p>
                <p className="text-xs text-neutral-400 truncate">{m.user?.email}</p>
              </div>
              <select
                className="input w-36 text-xs py-1"
                value={m.role}
                onChange={e => updateMember.mutate({ memberId: m.id, data: { role: e.target.value as MemberRole } })}
                disabled={m.id === memberId}
              >
                {(['admin', 'member', 'limited'] as MemberRole[]).map(r => (
                  <option key={r} value={r}>{ROLE_LABELS[r]}</option>
                ))}
              </select>
              {m.id !== memberId && (
                <button
                  onClick={() => { if (confirm(`Удалить «${m.user?.name}» из дома?`)) removeMember.mutate(m.id) }}
                  className="w-7 h-7 rounded-lg bg-red-100 text-red-500 hover:bg-red-200 flex items-center justify-center flex-shrink-0"
                >
                  <Trash2 size={13} />
                </button>
              )}
            </div>

            {m.role === 'limited' && rooms.length > 0 && (
              <div className="pt-1 border-t border-beige-200">
                <p className="text-xs text-neutral-500 mb-1.5">Доступные комнаты:</p>
                <div className="flex flex-wrap gap-1">
                  {rooms.map(room => {
                    const allowed = (m.allowed_room_ids ?? []).includes(room.id)
                    return (
                      <button
                        key={room.id}
                        onClick={() => toggleAllowedRoom(m, room.id)}
                        disabled={m.id === memberId}
                        className={`flex items-center gap-1 px-2 py-1 rounded-lg text-xs font-medium transition-all ${
                          allowed
                            ? 'bg-forest-100 text-forest-700 border border-forest-300'
                            : 'bg-beige-100 text-neutral-400 border border-beige-200 hover:bg-beige-200'
                        }`}
                      >
                        {room.icon} {room.name}
                        {allowed && <Check size={10} />}
                      </button>
                    )
                  })}
                </div>
                {(m.allowed_room_ids ?? []).length === 0 && (
                  <p className="text-xs text-amber-600 mt-1">Нет доступа ни к одной комнате</p>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

// ---- Knowledge Tab ----
const emptyAdvice = { title: '', content: '', steps: [] as string[], room_names: [] as string[], task_keywords: [] as string[], season: '' as string, category: 'regular' }

function KnowledgeTab() {
  const qc = useQueryClient()
  const { data: advices = [], isLoading } = useQuery({ queryKey: ['advice'], queryFn: () => adviceApi.list() })
  const [editId, setEditId] = useState<string | null>(null)
  const [form, setForm] = useState({ ...emptyAdvice })
  const [stepsText, setStepsText] = useState('')
  const [adding, setAdding] = useState(false)

  const openEdit = (a: Advice) => {
    setEditId(a.id)
    setForm({ title: a.title, content: a.content, steps: a.steps, room_names: a.room_names, task_keywords: a.task_keywords, season: a.season ?? '', category: a.category })
    setStepsText(a.steps.join('\n'))
    setAdding(false)
  }
  const openAdd = () => { setEditId(null); setForm({ ...emptyAdvice }); setStepsText(''); setAdding(true) }
  const closeForm = () => { setEditId(null); setAdding(false) }

  const getPayload = () => ({
    ...form,
    steps: stepsText.split('\n').map(s => s.trim()).filter(Boolean),
    room_names: form.room_names,
    task_keywords: form.task_keywords,
    season: form.season || null,
  })

  const create = useMutation({
    mutationFn: () => adviceApi.create(getPayload()),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['advice'] }); closeForm(); toast.success('Совет добавлен') },
    onError: () => toast.error('Ошибка'),
  })

  const update = useMutation({
    mutationFn: () => adviceApi.update(editId!, getPayload()),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['advice'] }); closeForm(); toast.success('Сохранено') },
    onError: () => toast.error('Ошибка'),
  })

  const del = useMutation({
    mutationFn: (id: string) => adviceApi.remove(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['advice'] }); toast.success('Совет удалён') },
    onError: () => toast.error('Ошибка'),
  })

  if (isLoading) return <div className="flex justify-center py-10"><Spinner className="w-6 h-6" /></div>

  return (
    <div className="space-y-4">
      {!adding && !editId && (
        <button onClick={openAdd} className="btn-primary px-4 py-2 text-sm flex items-center gap-2">
          <Plus size={15} /> Добавить совет
        </button>
      )}

      {(adding || editId) && (
        <div className="card space-y-3 max-w-2xl">
          <p className="font-medium text-sm">{adding ? 'Новый совет' : 'Редактировать совет'}</p>
          <input className="input" placeholder="Заголовок" value={form.title} onChange={e => setForm(f => ({ ...f, title: e.target.value }))} />
          <textarea className="input resize-none h-20" placeholder="Описание" value={form.content} onChange={e => setForm(f => ({ ...f, content: e.target.value }))} />
          <textarea className="input resize-none h-28 text-xs" placeholder="Шаги (каждый с новой строки)" value={stepsText} onChange={e => setStepsText(e.target.value)} />
          <div className="flex gap-2">
            <select className="input flex-1" value={form.category} onChange={e => setForm(f => ({ ...f, category: e.target.value }))}>
              {CATEGORY_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
            </select>
            <select className="input flex-1" value={form.season} onChange={e => setForm(f => ({ ...f, season: e.target.value }))}>
              {SEASON_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
            </select>
          </div>
          <input className="input text-xs" placeholder="Комнаты (через запятую): Кухня, Ванная" value={form.room_names.join(', ')} onChange={e => setForm(f => ({ ...f, room_names: e.target.value.split(',').map(s => s.trim()).filter(Boolean) }))} />
          <input className="input text-xs" placeholder="Ключевые слова задач (через запятую)" value={form.task_keywords.join(', ')} onChange={e => setForm(f => ({ ...f, task_keywords: e.target.value.split(',').map(s => s.trim()).filter(Boolean) }))} />
          <div className="flex gap-2">
            <button onClick={() => adding ? create.mutate() : update.mutate()} disabled={!form.title.trim() || create.isPending || update.isPending} className="btn-primary px-4 py-2 text-sm">
              {(create.isPending || update.isPending) ? <Spinner className="w-4 h-4" /> : 'Сохранить'}
            </button>
            <button onClick={closeForm} className="btn-secondary px-4 py-2 text-sm">Отмена</button>
          </div>
        </div>
      )}

      <div className="space-y-2">
        {advices.map(a => (
          <div key={a.id} className="card flex items-start gap-3">
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate">{a.title}</p>
              <p className="text-xs text-neutral-400 truncate">{a.content.slice(0, 80)}{a.content.length > 80 ? '…' : ''}</p>
              <p className="text-xs text-neutral-300 mt-0.5">{a.category} · {a.season ?? 'всесезонный'} · {a.steps.length} шагов</p>
            </div>
            <div className="flex gap-1 flex-shrink-0">
              <button onClick={() => openEdit(a)} className="w-7 h-7 rounded-lg bg-beige-200 text-neutral-500 hover:bg-beige-300 flex items-center justify-center"><Pencil size={13} /></button>
              <button onClick={() => { if (confirm(`Удалить «${a.title}»?`)) del.mutate(a.id) }} className="w-7 h-7 rounded-lg bg-red-100 text-red-500 hover:bg-red-200 flex items-center justify-center"><Trash2 size={13} /></button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

// ---- Main Admin Page ----
export default function Admin() {
  const [tab, setTab] = useState<Tab>('house')
  const { data: members = [] } = useMembers()
  const memberId = useAuthStore(s => s.memberId)

  const currentMember = useMemo(() => members.find(m => m.id === memberId), [members, memberId])
  const isAdmin = currentMember?.role === 'admin'

  const TABS: { id: Tab; label: string }[] = [
    { id: 'house', label: 'Дом' },
    { id: 'rooms', label: 'Комнаты' },
    { id: 'members', label: 'Участники' },
    { id: 'knowledge', label: 'База знаний' },
  ]

  return (
    <div className="space-y-5">
      <h1 className="font-display text-2xl text-forest-500">Администрирование</h1>

      <AdminGuard isAdmin={isAdmin}>
        <div className="flex gap-1 flex-wrap">
          {TABS.map(t => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${
                tab === t.id ? 'bg-forest-400 text-white' : 'bg-beige-200 text-neutral-600 hover:bg-beige-300'
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>

        <div className="mt-4">
          {tab === 'house' && <HouseTab />}
          {tab === 'rooms' && <RoomsTab />}
          {tab === 'members' && <MembersTab />}
          {tab === 'knowledge' && <KnowledgeTab />}
        </div>
      </AdminGuard>
    </div>
  )
}
