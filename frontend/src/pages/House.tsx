import { useState, useRef, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { Plus, Pencil, Trash2, Copy, Check } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { useRooms, useCreateRoom, useUpdateRoom, useDeleteRoom } from '../hooks/useRooms'
import { useMembers, useUpdateMember } from '../hooks/useMembers'
import { housesApi } from '../api/houses'
import { Modal } from '../components/ui/Modal'
import { Button } from '../components/ui/Button'
import { useAuthStore } from '../store/authStore'
import type { Room, MemberRole } from '../types'
import toast from 'react-hot-toast'

const ROLE_LABELS: Record<MemberRole, string> = { admin: 'Админ', member: 'Участник', limited: 'Гость' }

const COLOR_PALETTE = [
  '#4A7C59','#8DB596','#A8C5A0','#2D5A3D',
  '#F59E0B','#D97706','#FCD34D','#F97316',
  '#EF4444','#DC2626','#F87171','#EC4899',
  '#3B82F6','#2563EB','#60A5FA','#0EA5E9',
  '#8B5CF6','#7C3AED','#A78BFA','#6B7280',
]

const EMOJI_LIST = [
  '🏠','🛋️','🛏️','🚿','🛁','🍳','🍽️','🪴','🧹','🧺',
  '🪣','🔑','💡','🪟','🚪','📦','🧰','🔧','🔨','🪚',
  '🌿','🌻','🌸','🚗','🎮','📚','🧸','🎵','🖥️','📺',
  '🪑','🌡️','❄️','🔥','💧','🧲','💼','🎨','🪞','🏋️',
  '🧴','🪥','🧼','🛒','🧃','🍀','🌙','☀️','⭐','🎁',
]

function EmojiPicker({ value, onChange }: { value: string; onChange: (e: string) => void }) {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        onClick={() => setOpen(o => !o)}
        className="w-full input flex items-center gap-2 text-left"
      >
        <span className="text-2xl">{value || '🏠'}</span>
        <span className="text-sm text-neutral-500">Нажмите, чтобы выбрать иконку</span>
      </button>
      {open && (
        <div className="absolute z-50 mt-1 p-2 bg-white rounded-xl border border-beige-200 shadow-lg w-full">
          <div className="grid grid-cols-10 gap-1">
            {EMOJI_LIST.map(e => (
              <button
                key={e}
                type="button"
                onClick={() => { onChange(e); setOpen(false) }}
                className={`text-xl p-1 rounded-lg hover:bg-beige-100 transition-colors ${value === e ? 'bg-beige-200' : ''}`}
              >
                {e}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function RoomForm({ room, onClose }: { room?: Room; onClose: () => void }) {
  const [name, setName] = useState(room?.name ?? '')
  const [icon, setIcon] = useState(room?.icon ?? '🏠')
  const [color, setColor] = useState(room?.color ?? '#8DB596')
  const createRoom = useCreateRoom()
  const updateRoom = useUpdateRoom()

  const handleSave = async () => {
    if (!name.trim()) return toast.error('Введите название')
    try {
      if (room) {
        await updateRoom.mutateAsync({ roomId: room.id, data: { name, icon, color } })
        toast.success('Комната обновлена')
      } else {
        await createRoom.mutateAsync({ name, icon, color })
        toast.success('Комната создана')
      }
      onClose()
    } catch {
      toast.error('Ошибка сохранения')
    }
  }

  return (
    <div className="space-y-4">
      <div>
        <label className="label">Название</label>
        <input className="input" value={name} onChange={e => setName(e.target.value)} placeholder="Кухня" />
      </div>
      <div>
        <label className="label">Иконка</label>
        <EmojiPicker value={icon} onChange={setIcon} />
      </div>
      <div>
        <label className="label">Цвет</label>
        <div className="grid grid-cols-10 gap-1.5 mb-2">
          {COLOR_PALETTE.map(c => (
            <button
              key={c}
              type="button"
              onClick={() => setColor(c)}
              className="w-7 h-7 rounded-lg transition-transform hover:scale-110"
              style={{
                background: c,
                outline: color === c ? '2px solid #2D5A3D' : '2px solid transparent',
                outlineOffset: '2px',
              }}
            />
          ))}
        </div>
        <div className="flex gap-2 items-center">
          <input
            type="color"
            value={color}
            onChange={e => setColor(e.target.value)}
            className="w-8 h-8 rounded-lg cursor-pointer border-0"
            title="Произвольный цвет"
          />
          <span className="text-xs text-neutral-400">Или выберите произвольный</span>
          <span className="ml-auto font-mono text-xs text-neutral-500">{color}</span>
        </div>
      </div>
      <div className="flex gap-3">
        <Button variant="secondary" onClick={onClose} className="flex-1">Отмена</Button>
        <Button onClick={handleSave} className="flex-1" disabled={createRoom.isPending || updateRoom.isPending}>
          {room ? 'Сохранить' : 'Создать'}
        </Button>
      </div>
    </div>
  )
}

function InviteCodeCard({ houseId }: { houseId: string }) {
  const [copied, setCopied] = useState(false)
  const { data: house } = useQuery({
    queryKey: ['house', houseId],
    queryFn: () => housesApi.get(houseId),
  })

  const handleCopy = () => {
    if (!house?.invite_code) return
    navigator.clipboard.writeText(house.invite_code)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  if (!house) return null

  return (
    <div className="card bg-forest-50 border border-forest-200">
      <p className="text-sm font-medium text-neutral-700 mb-2">Код приглашения</p>
      <div className="flex items-center gap-3">
        <span className="font-mono text-2xl font-bold tracking-widest text-forest-600 flex-1">
          {house.invite_code}
        </span>
        <button
          onClick={handleCopy}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-forest-400 hover:bg-forest-500 text-white text-sm transition-colors"
        >
          {copied ? <Check size={14} /> : <Copy size={14} />}
          {copied ? 'Скопировано' : 'Копировать'}
        </button>
      </div>
      <p className="text-xs text-neutral-500 mt-2">
        Поделитесь этим кодом — новый участник вводит его при регистрации
      </p>
    </div>
  )
}

export default function House() {
  const { data: rooms = [] } = useRooms()
  const { data: members = [] } = useMembers()
  const deleteRoom = useDeleteRoom()
  const updateMember = useUpdateMember()

  const memberId = useAuthStore(s => s.memberId)
  const houseId = useAuthStore(s => s.houseId)
  const [roomModal, setRoomModal] = useState(false)
  const [editRoom, setEditRoom] = useState<Room | null>(null)

  const currentMember = members.find(m => m.id === memberId)
  const isAdmin = currentMember?.role === 'admin'

  const handleDeleteRoom = async (room: Room) => {
    if (!confirm(`Удалить комнату "${room.name}"?`)) return
    try {
      await deleteRoom.mutateAsync(room.id)
      toast.success('Комната удалена')
    } catch {
      toast.error('Ошибка удаления')
    }
  }

  const handleRoleChange = async (memberId: string, role: MemberRole) => {
    try {
      await updateMember.mutateAsync({ memberId, data: { role } })
      toast.success('Роль обновлена')
    } catch {
      toast.error('Ошибка обновления роли')
    }
  }

  return (
    <div className="space-y-8 max-w-2xl mx-auto">
      <h1 className="font-display text-2xl text-forest-500">Дом</h1>

      <section>
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-display text-lg text-neutral-700">Комнаты</h2>
          {isAdmin && (
            <Button size="sm" onClick={() => { setEditRoom(null); setRoomModal(true) }}>
              <Plus size={16} className="mr-1 inline" /> Добавить
            </Button>
          )}
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
          {rooms.map(room => (
            <div key={room.id} className="relative group">
              <Link
                to={`/house/room/${room.id}`}
                className="card flex flex-col items-center gap-2 relative transition-all hover:shadow-hover hover:-translate-y-0.5"
              >
                <div
                  className="w-12 h-12 rounded-xl flex items-center justify-center text-2xl"
                  style={{ background: room.color + '33' }}
                >
                  {room.icon}
                </div>

                <p className="text-sm font-medium text-neutral-700 text-center">{room.name}</p>
                <p className="text-xs text-neutral-400 text-center">Открыть комнату</p>
              </Link>

              {isAdmin && (
                <div className="absolute top-2 right-2 hidden group-hover:flex gap-1 z-10">
                  <button
                    onClick={(e) => {
                      e.preventDefault()
                      e.stopPropagation()
                      setEditRoom(room)
                      setRoomModal(true)
                    }}
                    className="w-6 h-6 rounded bg-beige-200 hover:bg-beige-300 text-neutral-500 flex items-center justify-center"
                  >
                    <Pencil size={10} />
                  </button>

                  <button
                    onClick={(e) => {
                      e.preventDefault()
                      e.stopPropagation()
                      handleDeleteRoom(room)
                    }}
                    className="w-6 h-6 rounded bg-red-100 hover:bg-red-200 text-red-500 flex items-center justify-center"
                  >
                    <Trash2 size={10} />
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      </section>

      <section>
        <h2 className="font-display text-lg text-neutral-700 mb-4">Участники</h2>

        {isAdmin && houseId && <div className="mb-4"><InviteCodeCard houseId={houseId} /></div>}

        <div className="space-y-3">
          {members.map(member => (
            <div key={member.id} className="card flex items-center gap-4">
              <div
                className="w-10 h-10 rounded-full flex items-center justify-center text-white font-semibold text-sm flex-shrink-0"
                style={{ background: member.color }}
              >
                {member.user?.name?.[0] ?? '?'}
              </div>

              <div className="flex-1 min-w-0">
                <p className="font-medium text-sm text-neutral-800">{member.user?.name ?? 'N/A'}</p>
                <p className="text-xs text-neutral-400">{member.user?.email ?? ''}</p>
              </div>

              {isAdmin ? (
                <select
                  className="input w-32 text-xs py-1.5"
                  value={member.role}
                  onChange={e => handleRoleChange(member.id, e.target.value as MemberRole)}
                >
                  {(['admin', 'member', 'limited'] as MemberRole[]).map(r => (
                    <option key={r} value={r}>{ROLE_LABELS[r]}</option>
                  ))}
                </select>
              ) : (
                <span className="text-xs text-neutral-500 bg-beige-100 px-2 py-1 rounded-lg">
                  {ROLE_LABELS[member.role]}
                </span>
              )}
            </div>
          ))}
        </div>
      </section>

      <Modal
        open={roomModal}
        onClose={() => { setRoomModal(false); setEditRoom(null) }}
        title={editRoom ? 'Редактировать комнату' : 'Новая комната'}
      >
        <RoomForm room={editRoom ?? undefined} onClose={() => { setRoomModal(false); setEditRoom(null) }} />
      </Modal>
    </div>
  )
}
