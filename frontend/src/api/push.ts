import client from './client'

interface PushSubscriptionPayload {
  endpoint: string
  keys: { p256dh: string; auth: string }
  user_agent?: string
}

export const pushApi = {
  getVapidPublicKey: (): Promise<string> =>
    client.get<{ public_key: string }>('/push/vapid-public-key').then(r => r.data.public_key),

  subscribe: (payload: PushSubscriptionPayload): Promise<void> =>
    client.post('/push/subscribe', payload).then(() => undefined),

  unsubscribe: (): Promise<void> =>
    client.delete('/push/unsubscribe').then(() => undefined),
}

export function urlBase64ToUint8Array(base64String: string): ArrayBuffer {
  const padding = '='.repeat((4 - (base64String.length % 4)) % 4)
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/')
  const rawData = atob(base64)
  const buf = new ArrayBuffer(rawData.length)
  const output = new Uint8Array(buf)
  for (let i = 0; i < rawData.length; i++) {
    output[i] = rawData.charCodeAt(i)
  }
  return buf
}
