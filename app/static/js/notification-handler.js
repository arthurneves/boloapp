// Função para registrar o service worker
async function registerServiceWorker() {
    if ('serviceWorker' in navigator) {
        try {
            // Verificar se já existe um service worker registrado
            const existingRegistration = await navigator.serviceWorker.getRegistration();
            if (existingRegistration && existingRegistration.active) {
                console.log('Service Worker já está registrado e ativo');
                return existingRegistration;
            }

            // Tentar registrar o novo service worker
            // Remover registros antigos
            const registrations = await navigator.serviceWorker.getRegistrations();
            for (let reg of registrations) {
                await reg.unregister();
            }
            console.log('Registros antigos removidos');

            // Registrar o novo service worker
            console.log('Registrando service worker...');
            const registration = await navigator.serviceWorker.register('/service-worker.js', {
                scope: '/'
            });
            console.log('Service worker registrado:', registration);

            // Forçar ativação
            if (registration.waiting) {
                registration.waiting.postMessage({ type: 'SKIP_WAITING' });
            }
            
            // Aguardar até que tenhamos um service worker ativo
            if (!registration.active) {
                await new Promise((resolve) => {
                    registration.addEventListener('activate', (event) => {
                        console.log('Service Worker ativado:', event);
                        resolve();
                    });
                });
            }
            
            console.log('Service Worker registrado com sucesso:', registration);
            return registration;
        } catch (error) {
            console.error('Erro ao registrar o Service Worker:', error);
            return null;
        }
    } else {
        console.warn('Service Worker não é suportado neste navegador');
        return null;
    }
}

// Função para atualizar o status exibido no botão
function updateNotificationStatus(message, isError = false) {
    const statusEl = document.getElementById('notification-status');
    if (statusEl) {
        statusEl.textContent = message;
        statusEl.style.color = isError ? '#dc3545' : '#ffffff';
    }
}

// Função para solicitar permissão para notificações
async function requestNotificationPermission() {
    if (!('Notification' in window)) {
        console.warn('Este navegador não suporta notificações');
        updateNotificationStatus('Navegador não suporta notificações', true);
        return false;
    }

    if (Notification.permission === 'granted') {
        return true;
    }

    if (Notification.permission !== 'denied') {
        updateNotificationStatus('Aguardando permissão...');
        const permission = await Notification.requestPermission();
        return permission === 'granted';
    }

    updateNotificationStatus('Permissão negada', true);
    return false;
}

// Classe para gerenciar o cache de notificações
class NotificationCache {
    static CACHE_KEY = 'notification_subscription_cache';
    static CACHE_DURATION = 24 * 60 * 60 * 1000; // 24 horas em milissegundos

    static async get() {
        try {
            const cached = localStorage.getItem(this.CACHE_KEY);
            if (!cached) return null;
            
            const parsedCache = JSON.parse(cached);
            if (!parsedCache || !parsedCache.timestamp || !parsedCache.subscription) {
                return null;
            }
            
            return parsedCache;
        } catch (error) {
            console.error('Erro ao ler cache:', error);
            return null;
        }
    }

    static async set(subscription) {
        try {
            const cacheData = {
                timestamp: Date.now(),
                subscription: subscription.toJSON()
            };
            localStorage.setItem(this.CACHE_KEY, JSON.stringify(cacheData));
            return true;
        } catch (error) {
            console.error('Erro ao salvar cache:', error);
            return false;
        }
    }

    static async hasValidCache() {
        const cache = await this.get();
        if (!cache) return false;
        return !this.isExpired(cache);
    }

    static isExpired(cache) {
        const now = Date.now();
        return (now - cache.timestamp) > this.CACHE_DURATION;
    }

    static async clear() {
        try {
            localStorage.removeItem(this.CACHE_KEY);
            return true;
        } catch (error) {
            console.error('Erro ao limpar cache:', error);
            return false;
        }
    }
}

// Cache da chave VAPID
let vapidKeyCache = null;

// Função para obter a chave VAPID do servidor
async function getVapidPublicKey() {
    try {
        // Retornar do cache se disponível
        if (vapidKeyCache) {
            console.log('Usando chave VAPID do cache');
            return vapidKeyCache;
        }

        updateNotificationStatus('Obtendo chave de registro...');
        const response = await fetch('/api/notificacoes/vapid-public-key');
        if (!response.ok) {
            throw new Error('Falha ao obter chave VAPID');
        }
        const data = await response.json();
        if (!data.publicKey) {
            throw new Error('Chave VAPID não encontrada na resposta');
        }

        // Armazenar no cache
        vapidKeyCache = data.publicKey;
        return vapidKeyCache;
    } catch (error) {
        console.error('Erro ao obter chave VAPID:', error);
        updateNotificationStatus('Erro ao obter chave de registro', true);
        throw error;
    }
}

// Função para comparar subscriptions
function areSubscriptionsEqual(sub1, sub2) {
    if (!sub1 || !sub2) return false;
    
    const sub1JSON = typeof sub1.toJSON === 'function' ? sub1.toJSON() : sub1;
    const sub2JSON = typeof sub2.toJSON === 'function' ? sub2.toJSON() : sub2;
    
    return sub1JSON.endpoint === sub2JSON.endpoint &&
           JSON.stringify(sub1JSON.keys) === JSON.stringify(sub2JSON.keys);
}

// Função para registrar o dispositivo para receber notificações push
async function subscribeToPushNotifications(swRegistration) {
    try {
        // Verificar cache primeiro
        const cache = await NotificationCache.get();
        if (cache && !NotificationCache.isExpired(cache)) {
            console.log('Usando subscription em cache');
            const existingSubscription = await swRegistration.pushManager.getSubscription();
            
            if (existingSubscription && areSubscriptionsEqual(existingSubscription, cache.subscription)) {
                console.log('Subscription atual igual ao cache, pulando registro');
                return existingSubscription;
            }
        }

        // Verificar se o navegador suporta notificações push
        if (!('PushManager' in window)) {
            console.warn('Push notifications não são suportadas neste navegador');
            updateNotificationStatus('Push notifications não suportadas', true);
            return null;
        }

        updateNotificationStatus('Verificando registro existente...');
        const existingSubscription = await swRegistration.pushManager.getSubscription();
        console.log('Verificando subscription existente:', existingSubscription);

        // Se já existe uma subscription válida, verifica se precisa atualizar
        if (existingSubscription) {
            console.log('Subscription existente encontrada');
            const cache = await NotificationCache.get();
            
            if (cache && areSubscriptionsEqual(existingSubscription, cache.subscription)) {
                console.log('Usando subscription em cache');
                return existingSubscription;
            }

            updateNotificationStatus('Atualizando registro existente...');
            const result = await sendSubscriptionToServer(existingSubscription);
            if (!result) {
                throw new Error('Falha ao atualizar registro no servidor');
            }
            return existingSubscription;
        }

        // Se não existe subscription, cria uma nova
        console.log('Obtendo chave VAPID do servidor...');
        const vapidPublicKey = await getVapidPublicKey();
        console.log('Chave VAPID obtida:', vapidPublicKey);
        const convertedVapidKey = urlBase64ToUint8Array(vapidPublicKey);
        console.log('Chave VAPID convertida (primeiros 10 bytes):', convertedVapidKey.slice(0, 10));

        updateNotificationStatus('Registrando dispositivo...');
        const subscription = await swRegistration.pushManager.subscribe({
            userVisibleOnly: true,
            applicationServerKey: convertedVapidKey
        });
        console.log('Nova subscription criada:', subscription);

        updateNotificationStatus('Salvando registro...');
        const result = await sendSubscriptionToServer(subscription);
        if (!result) {
            throw new Error('Falha ao salvar registro no servidor');
        }
        console.log('Registro salvo com sucesso:', result);
        return subscription;
    } catch (error) {
        console.error('Erro ao inscrever para notificações push:', error);
        updateNotificationStatus('Erro ao registrar notificações', true);
        return null;
    }
}

// Função para enviar a inscrição para o servidor
async function sendSubscriptionToServer(subscription) {
    try {
        const subscriptionJson = subscription.toJSON();
        console.log('Preparando subscription para envio:', subscriptionJson);
        
        const requestBody = {
            subscription: {
                endpoint: subscriptionJson.endpoint,
                expirationTime: subscriptionJson.expirationTime,
                keys: subscriptionJson.keys
            }
        };

        console.log('Payload a ser enviado:', JSON.stringify(requestBody, null, 2));

        const response = await fetch('/api/notificacoes/registrar-dispositivo', {
            method: 'POST',
            credentials: 'same-origin',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody)
        });

        if (response.redirected) {
            window.location.href = response.url;
            return null;
        }

        if (!response.ok) {
            if (response.status === 401) {
                sessionStorage.setItem('notification_auth_failed', 'true');
                await NotificationCache.clear();
                window.location.href = '/login';
                return null;
            }
            const data = await response.json();
            throw new Error(data.error || 'Erro ao registrar dispositivo');
        }

        sessionStorage.removeItem('notification_auth_failed');
        await NotificationCache.set(subscription);
        
        // Mostrar confirmação visual
        const button = document.getElementById('notification-prompt');
        const success = document.getElementById('notification-success');
        
        if (success && button) {
            success.style.display = 'flex';
            button.style.cursor = 'default';
            
            // Ocultar após 3 segundos
            setTimeout(() => {
                button.style.opacity = '0';
                setTimeout(() => {
                    button.style.display = 'none';
                }, 300);
            }, 3000);
        } else {
            updateNotificationStatus('Notificações ativadas com sucesso');
        }
        
        return await response.json();
    } catch (error) {
        console.error('Erro ao enviar inscrição:', error);
        updateNotificationStatus('Erro ao salvar registro', true);
        return null;
    }
}

// Função auxiliar para converter chaves VAPID
function urlBase64ToUint8Array(base64String) {
    const padding = '='.repeat((4 - base64String.length % 4) % 4);
    const base64 = (base64String + padding)
        .replace(/\-/g, '+')
        .replace(/_/g, '/');

    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);

    for (let i = 0; i < rawData.length; ++i) {
        outputArray[i] = rawData.charCodeAt(i);
    }
    return outputArray;
}

// Inicializar o sistema de notificações
async function initializeNotifications() {
    if (isInitializing) {
        console.log('Inicialização já em andamento, ignorando chamada duplicada');
        return;
    }

    isInitializing = true;
    try {
        updateNotificationStatus('Iniciando...');
        
        const permissionGranted = await requestNotificationPermission();
        if (!permissionGranted) {
            console.log('Permissão para notificações não concedida');
            return;
        }

        updateNotificationStatus('Configurando service worker...');
        const swRegistration = await registerServiceWorker();
        if (!swRegistration) {
            updateNotificationStatus('Falha ao configurar service worker', true);
            return;
        }

        if (!swRegistration.active) {
            updateNotificationStatus('Ativando service worker...');
            await new Promise((resolve) => {
                if (swRegistration.active) {
                    resolve();
                } else {
                    swRegistration.addEventListener('activate', () => {
                        console.log('Service Worker ativado com sucesso');
                        resolve();
                    });
                }
            });
        }

        const subscription = await subscribeToPushNotifications(swRegistration);
        if (!subscription) {
            updateNotificationStatus('Falha ao registrar notificações', true);
            return;
        }

        updateNotificationStatus('Notificações ativadas com sucesso');
        console.log('Sistema de notificações inicializado com sucesso');
    } catch (error) {
        console.error('Erro ao inicializar notificações:', error);
        updateNotificationStatus('Erro ao configurar notificações', true);
    } finally {
        isInitializing = false;
    }
}

// Variáveis de controle
let hasInitialized = false;
let isInitializing = false;

// Inicializar quando o documento estiver pronto
document.addEventListener('DOMContentLoaded', async function() {
    if (window.location.pathname.includes('/login')) {
        console.log('Página de login detectada, ignorando inicialização de notificações');
        return;
    }
    
    if (sessionStorage.getItem('notification_auth_failed')) {
        console.log('Falha de autenticação anterior detectada, aguardando nova autenticação');
        await NotificationCache.clear();
        return;
    }
    
    if (hasInitialized) {
        console.log('Sistema de notificações já foi inicializado');
        return;
    }

    // Verificar cache antes de inicializar
    const hasValidCache = await NotificationCache.hasValidCache();
    if (hasValidCache && Notification.permission === 'granted') {
        console.log('Cache válido encontrado, pulando inicialização');
        return;
    }
    
    const notificationButton = document.getElementById('notification-prompt');
    
    if (Notification.permission === 'granted' && !sessionStorage.getItem('notification_auth_failed')) {
        console.log('Permissão já concedida, inicializando...');
        hasInitialized = true;
        await initializeNotifications();
    } else if (notificationButton) {
        notificationButton.addEventListener('click', async function() {
            if (!hasInitialized) {
                hasInitialized = true;
                await initializeNotifications();
            }
        });
        console.log('Aguardando interação do usuário para inicializar notificações');
    }
});

window.addEventListener('load', function() {
    if (!window.location.pathname.includes('/login')) {
        sessionStorage.removeItem('notification_auth_failed');
    }
});
