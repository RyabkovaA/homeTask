import { useState } from 'react'
import { Plus, Pencil, Trash2 } from 'lucide-react'
import { useRooms, useCreateRoom, useUpdateRoom, useDeleteRoom } from '../hooks/useRooms'
import { useMembers, useUpdateMember } from '../hooks/useMembers'
import { Modal } from '../components/ui/Modal'
import { Button } from '../components/ui/Button'
import { Badge } from '../components/ui/Badge'
import type { Room, MemberRole } from '../types'
import toast from 'react-hot-toast'

const ROLE_LABELS: Record<MemberRole, string> = { admin: 'Админ', member: 'Участник', limited: 'Гость' }
const ROLE_VARIANTS: Record<MemberRole, 'success' | 'info' | 'default'> = {
  admin: 'success', member: 'info', limited: 'default'
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
        <input className="input" value={icon} onChange={e => setIcon(e.target.value)} placeholder="🏠" />
      </div>
      <div>
        <label className="label">Цвет</label>
        <div className="flex gap-2 items-center">
          <input type="color" value={color} onChange={e => setColor(e.target.value)} className="w-10 h-10 rounded-lg cursor-pointer" />
          <input className="input flex-1" value={color} onChange={e => setColor(e.target.value)} />
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

export default function House() {
  const { data: rooms = [] } = useRooms()
  const { data: members = [] } = useMembers()
  const deleteRoom = useDeleteRoom()
  const updateMember = useUpdateMember()

  const [roomModal, setRoomModal] = useState(false)
  const [editRoom, setEditRoom] = useState<Room | null>(null)

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

      {/* Rooms */}
      <section>
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-display text-lg text-neutral-700">Комнаты</h2>
          <Button size="sm" onClick={() => { setEditRoom(null); setRoomModal(true) }}>
            <Plus size={16} className="mr-1 inline" /> Добавить
          </Button>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
          {rooms.map(room => (
            <div key={room.id} className="card flex flex-col items-center gap-2 relative group">
              <div className="w-12 h-12 rounded-xl flex items-center justify-center text-2xl" style={{ background: room.color + '33' }}>
                {room.icon}
              </div>
              <p className="text-sm font-medium text-neutral-700 text-center">{room.name}</p>
              <div className="absolute top-2 right-2 hidden group-hover:flex gap-1">
                <button
                  onClick={() => { setEditRoom(room); setRoomModal(true) }}
                  className="w-6 h-6 rounded bg-beige-200 hover:bg-beige-300 text-neutral-500 flex items-center justify-center"
                >
                  <Pencil size={10} />
                </button>
                <button
                  onClick={() => handleDeleteRoom(room)}
                  className="w-6 h-6 rounded bg-red-100 hover:bg-red-200 text-red-500 flex items-center justify-center"
                >
                  <Trash2 size={10} />
                </button>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Members */}
      <section>
        <h2 className="font-display text-lg text-neutral-700 mb-4">Участники</h2>
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
              <select
                className="input w-32 text-xs py-1.5"
                value={member.role}
                onChange={e => handleRoleChange(member.id, e.target.value as MemberRole)}
              >
                {(['admin', 'member', 'limited'] as MemberRole[]).map(r => (
                  <option key={r} value={r}>{ROLE_LABELS[r]}</option>
                ))}
              </select>
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
