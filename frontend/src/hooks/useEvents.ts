import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { eventsApi } from '../api/events'
import { useAuthStore } from '../store/authStore'
import type { EventStatus } from '../types'

export function useEvents(fromDate?: string, toDate?: string) {
  const houseId = useAuthStore(s => s.houseId)
  return useQuery({
    queryKey: ['events', houseId, fromDate, toDate],
    queryFn: () => eventsApi.list(houseId!, fromDate, toDate),
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
