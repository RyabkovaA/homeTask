/// <reference lib="webworker" />
import { cleanupOutdatedCaches, precacheAndRoute } from 'workbox-precaching'
import { registerRoute } from 'workbox-routing'
import { NetworkFirst, CacheFirst } from 'workbox-strategies'
import { ExpirationPlugin } from 'workbox-expiration'

declare const self: ServiceWorkerGlobalScope & {
  __WB_MANIFEST: Array<{ url: string; revision: string | null }>
}

cleanupOutdatedCaches()
precacheAndRoute(self.__WB_MANIFEST)

// API GET: NetworkFirst — serve cached data when offline (5s network timeout)
registerRoute(
  ({ url, request }: { url: URL; request: Request }) =>
    url.pathname.startsWith('/api/v1/') && request.method === 'GET',
  new NetworkFirst({
    cacheName: 'api-get-v1',
    networkTimeoutSeconds: 5,
    plugins: [
      new ExpirationPlugin({ maxEntries: 100, maxAgeSeconds: 3600 }),
    ],
  })
)

// Google Fonts: CacheFirst (immutable, 1 year)
registerRoute(
  ({ url }: { url: URL }) =>
    url.origin === 'https://fonts.googleapis.com' ||
    url.origin === 'https://fonts.gstatic.com',
  new CacheFirst({
    cacheName: 'google-fonts-v1',
    plugins: [
      new ExpirationPlugin({ maxEntries: 20, maxAgeSeconds: 365 * 24 * 3600 }),
    ],
  })
)

// Push notification: show system notification
self.addEventListener('push', (event: Event) => {
  const pushEvent = event as PushEvent
  if (!pushEvent.data) return

  let payload: { title?: string; body?: string; data?: Record<string, string> }
  try {
    payload = pushEvent.data.json()
  } catch {
    payload = { title: 'HomeTask', body: pushEvent.data?.text() ?? '' }
  }

  pushEvent.waitUntil(
    self.registration.showNotification(payload.title ?? 'HomeTask', {
      body: payload.body ?? '',
      icon: '/icons/icon.svg',
      badge: '/icons/badge.svg',
      data: payload.data ?? { url: '/' },
    })
  )
})

// Notification click: focus existing tab or open new window
self.addEventListener('notificationclick', (event: Event) => {
  const notifEvent = event as NotificationEvent
  notifEvent.notification.close()
  const targetUrl = (notifEvent.notification.data as { url?: string } | null)?.url ?? '/'

  notifEvent.waitUntil(
    self.clients
      .matchAll({ type: 'window', includeUncontrolled: true })
      .then((clients) => {
        for (const client of clients) {
          if ('focus' in client) return (client as WindowClient).focus()
        }
        return self.clients.openWindow(targetUrl)
      })
  )
})
