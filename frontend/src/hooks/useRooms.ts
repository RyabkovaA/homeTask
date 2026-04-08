import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { roomsApi } from '../api/rooms'
import { useAuthStore } from '../store/authStore'

export function useRooms() {
  const houseId = useAuthStore(s => s.houseId)
  return useQuery({
    queryKey: ['rooms', houseId],
    queryFn: () => roomsApi.list(houseId!),
    enabled: !!houseId
  })
}

export function useCreateRoom() {
  const qc = useQueryClient()
  const houseId = useAuthStore(s => s.houseId)
  return useMutation({
    mutationFn: (data: { name: string; icon?: string; color?: string }) =>
      roomsApi.create(houseId!, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['rooms', houseId] })
  })
}

export function useUpdateRoom() {
  const qc = useQueryClient()
  const houseId = useAuthStore(s => s.houseId)
  return useMutation({
    mutationFn: ({ roomId, data }: { roomId: string; data: { name?: string; icon?: string; color?: string } }) =>
      roomsApi.update(roomId, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['rooms', houseId] })
  })
}

export function useDeleteRoom() {
  const qc = useQueryClient()
  const houseId = useAuthStore(s => s.houseId)
  return useMutation({
    mutationFn: (roomId: string) => roomsApi.delete(roomId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['rooms', houseId] })
  })
}
