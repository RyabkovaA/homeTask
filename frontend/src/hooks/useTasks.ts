import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { tasksApi } from '../api/tasks'
import { useAuthStore } from '../store/authStore'
import type { TaskFormData } from '../types'

export function useTasks() {
  const houseId = useAuthStore(s => s.houseId)
  return useQuery({
    queryKey: ['tasks', houseId],
    queryFn: () => tasksApi.list(houseId!),
    enabled: !!houseId,
    staleTime: 0,
  })
}

export function useCreateTask() {
  const qc = useQueryClient()
  const houseId = useAuthStore(s => s.houseId)
  return useMutation({
    mutationFn: (data: Partial<TaskFormData>) => tasksApi.create(houseId!, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['tasks', houseId] })
      qc.invalidateQueries({ queryKey: ['events', houseId] })
      qc.invalidateQueries({ queryKey: ['nudge', houseId] })
    }
  })
}

export function useUpdateTask() {
  const qc = useQueryClient()
  const houseId = useAuthStore(s => s.houseId)
  return useMutation({
    mutationFn: ({ taskId, data }: { taskId: string; data: Partial<TaskFormData> }) =>
      tasksApi.update(taskId, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['tasks', houseId] })
      qc.invalidateQueries({ queryKey: ['events', houseId] })
    }
  })
}

export function useDeleteTask() {
  const qc = useQueryClient()
  const houseId = useAuthStore(s => s.houseId)
  return useMutation({
    mutationFn: (taskId: string) => tasksApi.delete(taskId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['tasks', houseId] })
      qc.invalidateQueries({ queryKey: ['events', houseId] })
    }
  })
}
