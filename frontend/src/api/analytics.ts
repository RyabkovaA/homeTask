import client from './client'
import type { Analytics } from '../types'

export const analyticsApi = {
  get: (houseId: string, days = 30) =>
    client.get<Analytics>(`/houses/${houseId}/analytics`, { params: { days } }).then(r => r.data)
}
