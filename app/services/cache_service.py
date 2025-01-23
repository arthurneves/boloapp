from functools import wraps
from app import cache as global_cache

TIMEOUT = 36000

def cache_perfil_usuario(timeout=TIMEOUT):
    """
    Decorator personalizado para cache que considera autenticação
    e parâmetros específicos do usuário
    
    Args:
        timeout (int): Tempo de cache em segundos. Padrão: 300 = 5 minutos
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Gerar uma chave única que inclui o ID do usuário
            cache_key = f'{f.__name__}_{kwargs.get("id_usuario")}'
            
            # Tentar obter do cache
            rv = global_cache.get(cache_key)
            if rv is not None:
                return rv
            
            # Se não estiver no cache, executar a função e armazenar
            rv = f(*args, **kwargs)
            global_cache.set(cache_key, rv, timeout=timeout)
            return rv
        return decorated_function
    return decorator


def invalidar_cache_perfil_usuario(id_usuario):
    """
    Função para invalidar o cache do perfil de um usuário específico
    
    Args:
        id_usuario (int): ID do usuário cujo cache será invalidado
    """
    # Como o cache pode existir para diferentes usuários visualizando,
    # podemos usar um padrão para limpar todas as chaves relacionadas
    global_cache.delete_many('perfil_usuario_' + str(id_usuario))


def invalidar_cache_perfil():
    global_cache.delete_many('perfil_usuario_*')


def invalidar_cache_geral():
    global_cache.clear()
