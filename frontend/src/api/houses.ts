import client from './client'
import type { House } from '../types'

export const housesApi = {
  get: (houseId: string) =>
    client.get<House>(`/houses/${houseId}`).then(r => r.data),

  update: (houseId: string, data: { name: string }) =>
    client.patch<House>(`/houses/${houseId}`, data).then(r => r.data),

  create: (data: { name: string }) =>
    client.post<House>('/houses', data).then(r => r.data),
}
