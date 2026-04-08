import client from './client'
import type { TaskEvent, EventStatus, TaskHistoryItem } from '../types'

interface EventCreate {
  task_id: string
  occurrence_date: string
  status: EventStatus
  moved_to?: string | null
  note?: string | null
}

interface EventListFilters {
  fromDate?: string
  toDate?: string
  status?: EventStatus | ''
  roomId?: string
}

export const eventsApi = {
  list: (houseId: string, filters?: EventListFilters) => {
    const params: Record<string, string> = {}

    if (filters?.fromDate) params.from_date = filters.fromDate
    if (filters?.toDate) params.to_date = filters.toDate
    if (filters?.status) params.status = filters.status
    if (filters?.roomId) params.room_id = filters.roomId

    return client.get<TaskHistoryItem[]>(`/houses/${houseId}/events`, { params }).then(r => r.data)
  },

  create: (data: EventCreate) =>
    client.post<TaskEvent>('/events', data).then(r => r.data)
}