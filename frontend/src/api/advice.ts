import client from './client'
import type { Advice } from '../types'

interface AdviceCreate {
  title: string
  content: string
  steps: string[]
  room_names: string[]
  task_keywords: string[]
  season?: string | null
  category: string
}

export const adviceApi = {
  list: (room?: string) => {
    const params = room ? { room } : {}
    return client.get<Advice[]>('/advice', { params }).then(r => r.data)
  },

  create: (data: AdviceCreate) =>
    client.post<Advice>('/advice', data).then(r => r.data),

  update: (id: string, data: Partial<AdviceCreate> & { is_active?: boolean }) =>
    client.patch<Advice>(`/advice/${id}`, data).then(r => r.data),

  remove: (id: string) =>
    client.delete(`/advice/${id}`),
}
