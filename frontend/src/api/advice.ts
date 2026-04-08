import client from './client'
import type { Advice } from '../types'

export const adviceApi = {
  list: (room?: string) => {
    const params = room ? { room } : {}
    return client.get<Advice[]>('/advice', { params }).then(r => r.data)
  }
}
