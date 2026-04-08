import { useQuery } from '@tanstack/react-query'
import { adviceApi } from '../api/advice'

export function useAdvice(room?: string) {
  return useQuery({
    queryKey: ['advice', room],
    queryFn: () => adviceApi.list(room),
    staleTime: 5 * 60 * 1000
  })
}
