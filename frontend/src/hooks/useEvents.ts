import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { eventsApi } from '../api/events'
import { useAuthStore } from '../store/authStore'
import type { EventStatus } from '../types'

interface UseEventsFilters {
  fromDate?: string
  toDate?: string
  status?: EventStatus | ''
  roomId?: string
}

export function useEvents(filters?: UseEventsFilters) {
  const houseId = useAuthStore(s => s.houseId)

  return useQuery({
    queryKey: ['events', houseId, filters?.fromDate, filters?.toDate, filters?.status, filters?.roomId],
    queryFn: () => eventsApi.list(houseId!, filters),
    enabled: !!houseId
  })
}

export function useCreateEvent() {
  const qc = useQueryClient()
  const houseId = useAuthStore(s => s.houseId)

  return useMutation({
    mutationFn: (data: { task_id: string; occurrence_date: string; status: EventStatus; moved_to?: string | null; note?: string | null }) =>
      eventsApi.create(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['events', houseId] })
      qc.invalidateQueries({ queryKey: ['analytics', houseId] })
    }
  })
}