const CACHE_NAME = 'boloapp-v19';
const urlsToCache = [
  '/static/css/bootstrap.min.css',
  '/static/css/style-v3.css',
  '/static/js/scripts.js',
  '/static/js/chart.js',
  '/static/icons/bolo-coracao.png',
  '/static/favicon/favicon-32x32.png'
];

self.addEventListener('install', event => {
  self.skipWaiting(); // Ativar imediatamente
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(urlsToCache))
  );
});

self.addEventListener('activate', event => {
  console.log('[Service Worker] Ativado');
  
  // Tomar controle imediatamente
  event.waitUntil(
    Promise.all([
      self.clients.claim(),
      // Limpar caches antigos
      caches.keys().then(cacheNames => {
        return Promise.all(
          cacheNames
            .filter(cacheName => cacheName !== CACHE_NAME)
            .map(cacheName => caches.delete(cacheName))
        );
      })
    ])
  );
});

// Evento para receber notificações push
self.addEventListener('push', event => {
  console.log('[Service Worker] Push recebido');
  console.log('[Service Worker] Dados brutos:', event.data ? event.data.text() : 'Sem dados');
  
  let data = {};
  if (event.data) {
    try {
      const rawData = event.data.text();
      console.log('[Service Worker] Dados brutos:', rawData);
      data = JSON.parse(rawData);
      console.log('[Service Worker] Dados processados:', data);
    } catch (e) {
      console.error('[Service Worker] Erro ao processar JSON:', e);
      console.log('[Service Worker] Tentando usar texto bruto');
      data = {
        title: 'Nova notificação',
        body: event.data.text()
      };
    }
  } else {
    console.error('[Service Worker] Nenhum dado recebido no evento push');
  }
  
  const title = data.title || 'BoloApp';
  const options = {
    body: data.body || 'Você recebeu uma nova notificação',
    icon: '/static/icons/bolo-coracao.png',
    badge: '/static/favicon/favicon-32x32.png',
    data: data.url || '/',
    vibrate: [100, 50, 100],
    actions: [
      {
        action: 'explore',
        title: 'Ver detalhes'
      },
      {
        action: 'close',
        title: 'Fechar'
      }
    ]
  };
  
  event.waitUntil(
    self.registration.showNotification(title, options)
      .then(() => {
        console.log('[Service Worker] Notificação exibida com sucesso');
      })
      .catch(error => {
        console.error('[Service Worker] Erro ao exibir notificação:', error);
      })
  );
});

// Evento para lidar com cliques nas notificações
self.addEventListener('notificationclick', event => {
  console.log('[Service Worker] Clique na notificação', event);
  
  event.notification.close();
  
  if (event.action === 'explore') {
    event.waitUntil(
      clients.openWindow(event.notification.data)
    );
  } else if (event.action === 'close') {
    return;
  } else {
    event.waitUntil(
      clients.openWindow(event.notification.data)
    );
  }
});

// Interceptar requisições de rede
self.addEventListener('fetch', event => {
  // Não interceptar requisições de outros domínios
  if (!event.request.url.startsWith(self.location.origin)) {
    return;
  }

  // Ignorar requisições de API e autenticação
  if (
    event.request.url.includes('/api/') ||
    event.request.url.includes('/login') ||
    event.request.url === self.location.origin + '/'
  ) {
    return;
  }

  // Apenas interceptar recursos estáticos
  if (
    !event.request.url.includes('/static/') &&
    !event.request.url.includes('/favicon/')
  ) {
    return;
  }

  event.respondWith(
    caches.match(event.request).then(response => {
      // Cache-first strategy
      if (response) {
        return response;
      }

      // Buscar na rede se não estiver no cache
      return fetch(event.request).then(networkResponse => {
        // Não fazer cache de erros
        if (!networkResponse || networkResponse.status !== 200) {
          return networkResponse;
        }

        // Clonar e armazenar no cache apenas se for uma resposta básica
        if (networkResponse.type === 'basic') {
          const responseToCache = networkResponse.clone();
          caches.open(CACHE_NAME)
            .then(cache => {
              cache.put(event.request, responseToCache);
            });
        }

        return networkResponse;
      }).catch(error => {
        console.error('[Service Worker] Erro na requisição:', error);
        throw error;
      });
    })
  );
});
