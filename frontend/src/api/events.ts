import client from './client'
import type { TaskEvent, EventStatus } from '../types'

interface EventCreate {
  task_id: string
  occurrence_date: string
  status: EventStatus
  moved_to?: string | null
  note?: string | null
}

export const eventsApi = {
  list: (houseId: string, fromDate?: string, toDate?: string) => {
    const params: Record<string, string> = {}
    if (fromDate) params.from_date = fromDate
    if (toDate) params.to_date = toDate
    return client.get<TaskEvent[]>(`/houses/${houseId}/events`, { params }).then(r => r.data)
  },

  create: (data: EventCreate) =>
    client.post<TaskEvent>('/events', data).then(r => r.data)
}
