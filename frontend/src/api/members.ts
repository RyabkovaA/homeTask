import client from './client'
import type { Member, MemberRole } from '../types'

export const membersApi = {
  list: (houseId: string) =>
    client.get<Member[]>(`/houses/${houseId}/members`).then(r => r.data),

  update: (memberId: string, data: { role?: MemberRole; color?: string }) =>
    client.patch<Member>(`/members/${memberId}`, data).then(r => r.data),

  remove: (memberId: string) =>
    client.delete(`/members/${memberId}`)
}
