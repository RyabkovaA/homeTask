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
    enabled: !!houseId,
    staleTime: 0,
  })
}

function useInvalidateEventRelated() {
  const qc = useQueryClient()
  const houseId = useAuthStore(s => s.houseId)
  return () => {
    qc.invalidateQueries({ queryKey: ['events', houseId] })
    qc.invalidateQueries({ queryKey: ['analytics', houseId] })
    qc.invalidateQueries({ queryKey: ['nudge', houseId] })
  }
}

export function useCreateEvent() {
  const invalidate = useInvalidateEventRelated()

  return useMutation({
    mutationFn: (data: { task_id: string; occurrence_date: string; status: EventStatus; moved_to?: string | null; note?: string | null }) =>
      eventsApi.create(data),
    onSuccess: invalidate,
  })
}

export function useUpdateEvent() {
  const invalidate = useInvalidateEventRelated()

  return useMutation({
    mutationFn: ({ taskId, occurrenceDate, status, moved_to, note }: {
      taskId: string
      occurrenceDate: string
      status: EventStatus
      moved_to?: string | null
      note?: string | null
    }) => eventsApi.update(taskId, occurrenceDate, { status, moved_to, note }),
    onSuccess: invalidate,
  })
}