import client from './client'
import type { RagAdvice, HabitInsights } from '../types'

export const ragApi = {
  getTaskAdvice: (houseId: string, taskId: string) =>
    client
      .post<RagAdvice>(`/houses/${houseId}/tasks/${taskId}/rag-advice`)
      .then(r => r.data),

  getHabitInsights: (houseId: string, days = 30) =>
    client
      .get<HabitInsights>(`/houses/${houseId}/habit-insights`, { params: { days } })
      .then(r => r.data),
}
