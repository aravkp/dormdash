// Basic service worker with notification click handler
self.addEventListener('install', (event) => {
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(self.clients.claim());
});

// keep default network behaviour
self.addEventListener('fetch', (event) => {
  // noop - let the browser handle network requests
});

// ensure notifications open app on click (open customer.html)
self.addEventListener('notificationclick', function(event) {
  event.notification.close();
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then(clientList => {
      for (const client of clientList) {
        // focus any open client
        if (client.url && 'focus' in client) {
          return client.focus();
        }
      }
      // otherwise open customer page
      if (clients.openWindow) {
        return clients.openWindow('/customer.html');
      }
    })
  );
});