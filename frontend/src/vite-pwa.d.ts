// Type stubs for vite-plugin-pwa virtual modules.
// Replaced by the real declarations once `npm install` is run.

declare module 'virtual:pwa-register/react' {
  export interface RegisterSWOptions {
    immediate?: boolean
    onNeedRefresh?: () => void
    onOfflineReady?: () => void
    onRegistered?: (reg: ServiceWorkerRegistration | undefined) => void
    onRegisterError?: (error: unknown) => void
  }
  export function useRegisterSW(options?: RegisterSWOptions): {
    needRefresh: import('react').MutableRefObject<boolean>
    offlineReady: import('react').MutableRefObject<boolean>
    updateServiceWorker: (reloadPage?: boolean) => Promise<void>
  }
}

declare module 'virtual:pwa-register' {
  export interface RegisterSWOptions {
    immediate?: boolean
    onNeedRefresh?: () => void
    onOfflineReady?: () => void
    onRegistered?: (reg: ServiceWorkerRegistration | undefined) => void
    onRegisterError?: (error: unknown) => void
  }
  export function registerSW(options?: RegisterSWOptions): (reloadPage?: boolean) => Promise<void>
}
