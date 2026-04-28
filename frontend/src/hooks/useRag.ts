import { useMutation, useQuery } from '@tanstack/react-query'
import { ragApi } from '../api/rag'
import { useAuthStore } from '../store/authStore'

export function useTaskRagAdvice() {
  const houseId = useAuthStore(s => s.houseId)
  return useMutation({
    mutationFn: (taskId: string) => ragApi.getTaskAdvice(houseId!, taskId),
  })
}

export function useHabitInsights(days = 30, enabled = true) {
  const houseId = useAuthStore(s => s.houseId)
  return useQuery({
    queryKey: ['habit-insights', houseId, days],
    queryFn: () => ragApi.getHabitInsights(houseId!, days),
    enabled: !!houseId && enabled,
    staleTime: 2 * 60 * 1000,
  })
}

export function useSuggestTasks() {
  const houseId = useAuthStore(s => s.houseId)
  return useMutation({
    mutationFn: () => ragApi.suggestTasks(houseId!),
  })
}

export function useNudge(enabled = true) {
  const houseId = useAuthStore(s => s.houseId)
  return useQuery({
    queryKey: ['nudge', houseId],
    queryFn: () => ragApi.getNudge(houseId!),
    enabled: !!houseId && enabled,
    staleTime: 5 * 60 * 1000,
  })
}

export function useCompletionProbability(taskId: string | null, enabled = true) {
  const houseId = useAuthStore(s => s.houseId)
  return useQuery({
    queryKey: ['completion-probability', houseId, taskId],
    queryFn: () => ragApi.getCompletionProbability(houseId!, taskId!),
    enabled: !!houseId && !!taskId && enabled,
    staleTime: 10 * 60 * 1000,
  })
}
