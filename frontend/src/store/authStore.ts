import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface AuthState {
  token: string | null
  houseId: string | null
  memberId: string | null
  userName: string | null
  setAuth: (token: string, houseId: string, memberId: string, userName: string) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    set => ({
      token: null,
      houseId: null,
      memberId: null,
      userName: null,
      setAuth: (token, houseId, memberId, userName) =>
        set({ token, houseId, memberId, userName }),
      logout: () => set({ token: null, houseId: null, memberId: null, userName: null })
    }),
    { name: 'hometask-auth' }
  )
)
