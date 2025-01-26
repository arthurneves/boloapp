const CACHE_NAME = 'boloapp-v7';
const urlsToCache = [
  '/',
  '/static/css/bootstrap.min.css',
  '/static/css/style-v2.css',
  '/static/js/jquery-3.6.0.min.js',
  '/static/js/bootstrap.bundle.min.js',
  '/static/icons/bolo-coracao.png'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(urlsToCache))
  );
});

self.addEventListener('fetch', event => {
  console.log('Interceptando requisição para:', event.request.url);

  event.respondWith(
    caches.match(event.request)
      .then(response => {
        // Primeiro tenta o cache
        if (response) {
          // Check if the cached version matches the current cache name
          if (response.headers.get('cache-name') !== CACHE_NAME) {

            // Faz uma busca em background para atualizar
            fetch(event.request).then(networkResponse => {
              if (networkResponse.status === 200) {
                caches.open(CACHE_NAME).then(cache => {
                  cache.put(event.request, networkResponse.clone());
                });
              }
            });
            return response;

          }
        }
        
        // Se não estiver no cache, busca na rede
        return fetch(event.request).then(response => {
          // Só faz cache de respostas bem-sucedidas
          if (!response || response.status !== 200 || response.type !== 'basic') {
            return response;
          }

          const responseToCache = response.clone();
          caches.open(CACHE_NAME)
            .then(cache => {
              cache.put(event.request, responseToCache);
            });

          return response;
        });
      })
  );
});

self.addEventListener('activate', event => {
  const cacheWhitelist = [CACHE_NAME];
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheWhitelist.indexOf(cacheName) === -1) {
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => {
      return self.clients.claim(); // Garante que o novo Service Worker tome controle imediatamente
    })
  );
});
