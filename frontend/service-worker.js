importScripts('https://www.gstatic.com/firebasejs/12.11.0/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/12.11.0/firebase-messaging-compat.js');

firebase.initializeApp({
  apiKey: "AIzaSyCmHbirJJE7d8_wvMhvEUDknBfSdTqwPK0",
  authDomain: "dormdash-38623.firebaseapp.com",
  projectId: "dormdash-38623",
  storageBucket: "dormdash-38623.firebasestorage.app",
  messagingSenderId: "927323489495",
  appId: "1:927323489495:web:0f9a2163ab45b25f509c92"
});

const firebaseMessaging = firebase.messaging();

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

firebaseMessaging.onBackgroundMessage(function(payload) {
  const title = payload.notification?.title || 'DormDash';
  const options = {
    body: payload.notification?.body || '',
    icon: 'icon-512.png',
    badge: 'icon-512.png',
    data: {
      url: payload.fcmOptions?.link || '/customer.html'
    }
  };

  self.registration.showNotification(title, options);
});

// Ensure notifications reopen the relevant app page on click.
self.addEventListener('notificationclick', function(event) {
  event.notification.close();
  const targetUrl = event.notification.data && event.notification.data.url
    ? event.notification.data.url
    : '/customer.html';

  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then(clientList => {
      for (const client of clientList) {
        if (client.url && client.url.includes(targetUrl) && 'focus' in client) {
          return client.focus();
        }
      }
      if (clients.openWindow) {
        return clients.openWindow(targetUrl);
      }
    })
  );
});
