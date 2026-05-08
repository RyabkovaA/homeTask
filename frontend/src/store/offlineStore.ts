import { create } from 'zustand'

interface OfflineState {
  pendingCount: number
  isSyncing: boolean
  setPendingCount: (count: number) => void
  setIsSyncing: (v: boolean) => void
  incrementPending: () => void
  decrementPending: () => void
}

export const useOfflineStore = create<OfflineState>(set => ({
  pendingCount: 0,
  isSyncing: false,
  setPendingCount: (count) => set({ pendingCount: count }),
  setIsSyncing: (v) => set({ isSyncing: v }),
  incrementPending: () => set(s => ({ pendingCount: s.pendingCount + 1 })),
  decrementPending: () => set(s => ({ pendingCount: Math.max(0, s.pendingCount - 1) })),
}))
