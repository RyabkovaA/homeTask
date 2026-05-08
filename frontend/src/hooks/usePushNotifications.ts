import { useState, useEffect, useCallback } from 'react'
import { pushApi, urlBase64ToUint8Array } from '../api/push'

export type PushPermission = NotificationPermission | 'unsupported'

export function usePushNotifications() {
  const [permission, setPermission] = useState<PushPermission>(
    typeof Notification !== 'undefined' ? Notification.permission : 'unsupported'
  )
  const [isSubscribed, setIsSubscribed] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const isSupported =
    typeof window !== 'undefined' &&
    'serviceWorker' in navigator &&
    'PushManager' in window &&
    'Notification' in window

  // Check existing subscription on mount
  useEffect(() => {
    if (!isSupported) return
    navigator.serviceWorker.ready.then((reg) =>
      reg.pushManager.getSubscription().then((sub) => setIsSubscribed(!!sub))
    )
  }, [isSupported])

  const subscribe = useCallback(async (): Promise<'success' | 'denied' | 'error'> => {
    if (!isSupported) return 'error'
    setIsLoading(true)
    setError(null)
    try {
      const perm = await Notification.requestPermission()
      setPermission(perm)
      if (perm !== 'granted') return 'denied'

      const vapidKey = await pushApi.getVapidPublicKey()
      const reg = await navigator.serviceWorker.ready
      const sub = await reg.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(vapidKey),
      })

      const json = sub.toJSON() as {
        endpoint: string
        keys: { p256dh: string; auth: string }
      }
      await pushApi.subscribe({
        endpoint: json.endpoint,
        keys: json.keys,
        user_agent: navigator.userAgent.slice(0, 512),
      })
      setIsSubscribed(true)
      return 'success'
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Не удалось подключить уведомления')
      return 'error'
    } finally {
      setIsLoading(false)
    }
  }, [isSupported])

  const unsubscribe = useCallback(async (): Promise<boolean> => {
    if (!isSupported) return false
    setIsLoading(true)
    setError(null)
    try {
      const reg = await navigator.serviceWorker.ready
      const sub = await reg.pushManager.getSubscription()
      if (sub) await sub.unsubscribe()
      await pushApi.unsubscribe()
      setIsSubscribed(false)
      return true
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Не удалось отключить уведомления')
      return false
    } finally {
      setIsLoading(false)
    }
  }, [isSupported])

  return { permission, isSubscribed, isLoading, error, isSupported, subscribe, unsubscribe }
}
