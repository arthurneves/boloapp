from flask import request, current_app, g
from functools import wraps
from urllib.parse import urlencode
from app import cache as global_cache
from flask_login import current_user

TIMEOUT = 36000


# =============================================================================
# Geracao de Cache Key
# =============================================================================

def generate_cache_key(prefix: str) -> str:
    """
    Gera uma chave de cache usando um prefixo e os parâmetros de query ordenados.
    
    Args:
        prefix (str): Prefixo que identifica o tipo de cache.

    Returns:
        str: Chave de cache formatada.
    """
    args = request.args.to_dict()
    sorted_params = urlencode(sorted(args.items()))
    return f"{prefix}_{sorted_params}"


def make_cache_key_transacoes() -> str:
    return generate_cache_key("lista_transacoes")


def make_cache_key_promessas() -> str:
    return generate_cache_key("lista_promessas")


def make_cache_key_lista_usuarios() -> str:
    return generate_cache_key("lista_usuarios")


def make_cache_key_lista_usuarios_visao_adm() -> str:
    return generate_cache_key("lista_usuarios_visao_adm")


def make_cache_key_logs() -> str:
    return generate_cache_key("lista_logs")


# =============================================================================
# Cache Decorators
# =============================================================================

def cache_perfil_home(timeout: int = TIMEOUT):
    """
    Decorator que utiliza o cache para a página inicial do perfil do usuário.
    
    A chave é gerada a partir do ID do usuário logado.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = f"home_current_user_{current_user.id_usuario}"
            cached_result = global_cache.get(cache_key)
            if cached_result is not None:
                return cached_result

            result = func(*args, **kwargs)
            global_cache.set(cache_key, result, timeout=timeout)
            return result
        return wrapper
    return decorator


def cache_perfil_usuario(timeout: int = TIMEOUT):
    """
    Decorator que utiliza o cache para o perfil de um usuário específico.
    
    A chave é gerada a partir do nome da função e do ID do usuário (passado via kwargs).
    Se o ID do usuário não for fornecido, a função é executada normalmente.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            id_usuario = kwargs.get("id_usuario")
            if id_usuario is None:
                return func(*args, **kwargs)

            cache_key = f"{func.__name__}_{id_usuario}"
            cached_result = global_cache.get(cache_key)
            if cached_result is not None:
                return cached_result

            result = func(*args, **kwargs)
            global_cache.set(cache_key, result, timeout=timeout)
            return result
        return wrapper
    return decorator


# =============================================================================
# Funcoes de Invalidacao de Cache
# =============================================================================

def invalidar_cache(pattern: str) -> bool:
    """
    Invalida entradas de cache que correspondam ao padrão informado.
    
    Primeiro, tenta utilizar o Redis (se disponível). Caso contrário, utiliza o SimpleCache.
    
    Args:
        pattern (str): Padrão para as chaves a serem invalidada (ex.: '*lista_logs_*').

    Returns:
        bool: True se a invalidação ocorrer com sucesso, False caso contrário.
    """
    try:
        # Preferência para o Redis
        if hasattr(global_cache.cache, '_write_client'):
            redis_client = global_cache.cache._write_client
            matching_keys = list(redis_client.scan_iter(match=pattern))
            if matching_keys:
                pipeline = redis_client.pipeline()
                for key in matching_keys:
                    key_str = key.decode('utf-8') if isinstance(key, bytes) else key
                    current_app.logger.info(f"Deletando chave: {key_str}")
                    pipeline.delete(key)
                deleted_count = len(matching_keys)
                pipeline.execute()
                current_app.logger.info(f"Cache Redis invalidado: {deleted_count} chaves deletadas.")
                return True
            current_app.logger.info(f"Nenhuma chave encontrada para o padrão: {pattern}")

        # Fallback para SimpleCache
        elif hasattr(global_cache.cache, '_cache'):
            pattern_x = pattern.replace("*", "")
            keys_to_delete = [key for key in global_cache.cache._cache.keys() if pattern_x in key]
            for key in keys_to_delete:
                global_cache.delete(key)
            current_app.logger.info(f"Cache SimpleCache invalidado: {len(keys_to_delete)} entradas deletadas.")
            return True
        else:
            current_app.logger.error("Nenhum mecanismo de cache compatível encontrado.")
            return False
    except Exception as e:
        current_app.logger.error(f"Erro ao invalidar cache: {str(e)}")
        return False

# Foi legal de fazer e tem usos interessantes com o Flask g, porem a solucao mais simples e o timeout do cache para 5 minutos
# def invalidar_cache_lista_logs(func):
#     """
#     Decorator para invalidar o cache dos logs antes da execução da função.
    
#     Garante que a invalidação ocorra apenas uma vez por requisição.
#     """
#     @wraps(func)
#     def wrapper(*args, **kwargs):
#         if not getattr(g, 'log_limpo', False):
#             invalidar_cache('*lista_logs_*')
#             g.log_limpo = True
#         return func(*args, **kwargs)
#     return wrapper


def invalidar_cache_perfil_usuario(id_usuario):
    """
    Invalida o cache do perfil de um usuário específico.
    """
    global_cache.delete(f"perfil_usuario_{id_usuario}")


def invalidar_cache_home(id_usuario):
    """
    Invalida o cache da home do usuário.
    """
    global_cache.delete(f"home_current_user_{id_usuario}")


def invalidar_cache_usuarios():
    """
    Invalida caches relacionados aos usuários, tanto a lista quanto os perfis.
    """
    invalidar_cache('*lista_usuarios_*')
    invalidar_cache('*lista_usuarios_visao_adm_*')
    invalidar_cache('*perfil_usuario_*')


def invalidar_cache_lista_usuarios():
    """
    Invalida o cache da lista de usuários.
    """
    invalidar_cache('*lista_usuarios_*')


def invalidar_cache_lista_usuarios_visao_adm():
    """
    Invalida o cache da lista de usuários para visão administrativa.
    """
    invalidar_cache('*lista_usuarios_visao_adm_*')


def invalidar_cache_lista_promessa():
    """
    Invalida o cache da lista de promessas.
    """
    invalidar_cache('*lista_promessas_*')


def invalidar_cache_geral():
    """
    Limpa todas as entradas do cache.
    """
    global_cache.clear()
