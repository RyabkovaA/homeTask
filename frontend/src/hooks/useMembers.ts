import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { membersApi } from '../api/members'
import { useAuthStore } from '../store/authStore'
import type { MemberRole } from '../types'

export function useMembers() {
  const houseId = useAuthStore(s => s.houseId)
  return useQuery({
    queryKey: ['members', houseId],
    queryFn: () => membersApi.list(houseId!),
    enabled: !!houseId
  })
}

export function useInviteMember() {
  const qc = useQueryClient()
  const houseId = useAuthStore(s => s.houseId)
  return useMutation({
    mutationFn: (data: { email: string; role?: MemberRole; color?: string }) =>
      membersApi.invite(houseId!, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['members', houseId] })
  })
}

export function useUpdateMember() {
  const qc = useQueryClient()
  const houseId = useAuthStore(s => s.houseId)
  return useMutation({
    mutationFn: ({ memberId, data }: { memberId: string; data: { role?: MemberRole; color?: string; allowed_room_ids?: string[] } }) =>
      membersApi.update(memberId, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['members', houseId] })
  })
}

export function useRemoveMember() {
  const qc = useQueryClient()
  const houseId = useAuthStore(s => s.houseId)
  return useMutation({
    mutationFn: (memberId: string) => membersApi.remove(memberId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['members', houseId] })
  })
}
