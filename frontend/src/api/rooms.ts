import client from './client'
import type { Room } from '../types'

interface RoomCreate {
  name: string
  icon?: string
  color?: string
}

export const roomsApi = {
  list: (houseId: string) =>
    client.get<Room[]>(`/houses/${houseId}/rooms`).then(r => r.data),

  create: (houseId: string, data: RoomCreate) =>
    client.post<Room>(`/houses/${houseId}/rooms`, data).then(r => r.data),

  update: (roomId: string, data: Partial<RoomCreate>) =>
    client.patch<Room>(`/rooms/${roomId}`, data).then(r => r.data),

  delete: (roomId: string) =>
    client.delete(`/rooms/${roomId}`)
}
