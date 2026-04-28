import client from './client'
import type { RagAdvice, HabitInsights, TaskSuggestionsResponse, CompletionProbability, Nudge } from '../types'

export const ragApi = {
  getTaskAdvice: (houseId: string, taskId: string) =>
    client
      .post<RagAdvice>(`/houses/${houseId}/tasks/${taskId}/rag-advice`)
      .then(r => r.data),

  getHabitInsights: (houseId: string, days = 30) =>
    client
      .get<HabitInsights>(`/houses/${houseId}/habit-insights`, { params: { days } })
      .then(r => r.data),

  rateAdvice: (deliveryId: string, rating: 1 | -1 | 0) =>
    client
      .post<{ delivery_id: string; rating: number }>(`/rag/deliveries/${deliveryId}/rate`, { rating })
      .then(r => r.data),

  suggestTasks: (houseId: string) =>
    client
      .post<TaskSuggestionsResponse>(`/houses/${houseId}/suggest-tasks`)
      .then(r => r.data),

  getCompletionProbability: (houseId: string, taskId: string) =>
    client
      .get<CompletionProbability>(`/houses/${houseId}/tasks/${taskId}/completion-probability`)
      .then(r => r.data),

  getNudge: (houseId: string) =>
    client
      .get<Nudge>(`/houses/${houseId}/nudge`)
      .then(r => r.data),
}
