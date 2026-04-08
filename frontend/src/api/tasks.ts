import client from './client'
import type { Task, TaskFormData } from '../types'

export const tasksApi = {
  list: (houseId: string) =>
    client.get<Task[]>(`/houses/${houseId}/tasks`).then(r => r.data),

  create: (houseId: string, data: Partial<TaskFormData>) =>
    client.post<Task>(`/houses/${houseId}/tasks`, data).then(r => r.data),

  update: (taskId: string, data: Partial<TaskFormData>) =>
    client.patch<Task>(`/tasks/${taskId}`, data).then(r => r.data),

  delete: (taskId: string) =>
    client.delete(`/tasks/${taskId}`)
}
