import { useQuery } from '@tanstack/react-query'
import { analyticsApi } from '../api/analytics'
import { useAuthStore } from '../store/authStore'

export function useAnalytics(days = 30) {
  const houseId = useAuthStore(s => s.houseId)
  return useQuery({
    queryKey: ['analytics', houseId, days],
    queryFn: () => analyticsApi.get(houseId!, days),
    enabled: !!houseId
  })
}
