import axios from 'axios'
import client from './client'
import type { TaskEvent, EventStatus, TaskHistoryItem } from '../types'
import { enqueueEvent } from '../utils/offlineQueue'
import { useOfflineStore } from '../store/offlineStore'

interface EventCreate {
  task_id: string
  occurrence_date: string
  status: EventStatus
  moved_to?: string | null
  note?: string | null
}

interface EventPatch {
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

  // Direct API call — used during offline queue flush (no queuing on failure)
  createDirect: (data: EventCreate) =>
    client.post<TaskEvent>('/events', data).then(r => r.data),

  // Offline-aware create: tries network first, queues in IndexedDB if offline.
  // On 409 (event already exists for this occurrence) automatically PATCHes instead.
  create: async (data: EventCreate): Promise<TaskEvent | null> => {
    if (!navigator.onLine) {
      await enqueueEvent({ localId: crypto.randomUUID(), payload: data })
      useOfflineStore.getState().incrementPending()
      return null
    }
    try {
      return await client.post<TaskEvent>('/events', data).then(r => r.data)
    } catch (err: unknown) {
      if (axios.isAxiosError(err) && err.response?.status === 409) {
        // Event already exists — update it instead
        return eventsApi.update(data.task_id, data.occurrence_date, {
          status: data.status,
          moved_to: data.moved_to,
          note: data.note,
        })
      }
      const isNetworkError =
        axios.isAxiosError(err) && !err.response && (
          err.code === 'ERR_NETWORK' ||
          err.code === 'ECONNABORTED' ||
          err.message === 'Network Error'
        )
      if (isNetworkError) {
        await enqueueEvent({ localId: crypto.randomUUID(), payload: data })
        useOfflineStore.getState().incrementPending()
        return null
      }
      throw err
    }
  },

  update: (taskId: string, occurrenceDate: string, data: EventPatch): Promise<TaskEvent> =>
    client.patch<TaskEvent>(`/events/${taskId}/${occurrenceDate}`, data).then(r => r.data),
}
