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

export function useUpdateMember() {
  const qc = useQueryClient()
  const houseId = useAuthStore(s => s.houseId)
  return useMutation({
    mutationFn: ({ memberId, data }: { memberId: string; data: { role?: MemberRole; color?: string } }) =>
      membersApi.update(memberId, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['members', houseId] })
  })
}
