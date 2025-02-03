from functools import wraps
from flask import request, current_app
from urllib.parse import urlencode
from app import cache as global_cache

TIMEOUT = 36000

def make_cache_key_transacoes():
    args = request.args.to_dict()
    # Ordenar os parâmetros para garantir consistência na chave do cache
    key = "lista_transacoes_" + urlencode(sorted(args.items()))
    return key

def make_cache_key_promessas():
    args = request.args.to_dict()
    # Ordenar os parâmetros para garantir consistência na chave do cache
    key = "lista_promessas_" + urlencode(sorted(args.items()))
    return key



def cache_perfil_home(timeout=TIMEOUT):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):

            from flask_login import current_user
            cache_key = f'home_current_user_{current_user.id_usuario}'

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


def cache_perfil_usuario(timeout=TIMEOUT):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):

            id_usuario = kwargs.get("id_usuario")
            if id_usuario is None:
                return f(*args, **kwargs)

            # Gerar uma chave única que inclui o ID do usuário e o nome da função        
            cache_key = f'{f.__name__}_{id_usuario}'
            
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
    global_cache.delete('perfil_usuario_' + str(id_usuario))


def invalidar_cache_home(id_usuario):
    global_cache.delete('home_current_user_' + str(id_usuario))


def invalidar_cache_perfil_geral():
    global_cache.delete_many('perfil_usuario_*')


def invalidar_cache_lista_promessa():
    try:
        deleted_count = 0
        keys_to_delete = []
        
        # Different cache backends store keys differently
        # Try to get cached keys based on the backend type
        if hasattr(global_cache.cache, '_cache'):
            # Simple cache backend
            source_keys = global_cache.cache._cache.keys()
        elif hasattr(global_cache.cache, 'get_backend_keys'):
            # Redis or other backend with get_backend_keys support
            source_keys = global_cache.cache.get_backend_keys()
        else:
            # Fallback: delete using delete_many
            current_app.logger.info('Using fallback cache invalidation method')
            return global_cache.delete_many('lista_promessas_*')
        
        # First, collect all keys that need to be deleted
        for key in source_keys:
            # Convert bytes to str if necessary (for Redis)
            if isinstance(key, bytes):
                key = key.decode('utf-8')
            
            if isinstance(key, str) and key.startswith('lista_promessas_'):
                keys_to_delete.append(key)
        
        # Then delete them in a separate loop
        for key in keys_to_delete:
            global_cache.delete(key)
            deleted_count += 1
            current_app.logger.info(f'Cache deleted for key: {key}')
        
        current_app.logger.info(f'Successfully invalidated {deleted_count} promise list cache entries')
        return True
    except Exception as e:
        current_app.logger.error(f'Error invalidating promise list cache: {str(e)}')
        return False

def invalidar_cache_geral():
    global_cache.clear()
