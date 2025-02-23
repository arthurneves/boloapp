from flask import request, current_app, g
from functools import wraps
from urllib.parse import urlencode
from app import cache as global_cache

TIMEOUT = 36000


###
#   MONTAGEM DE KEYS DE CACHE
###

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

def make_cache_key_lista_usuarios():
    args = request.args.to_dict()
    # Ordenar os parâmetros para garantir consistência na chave do cache
    key = "lista_usuarios_" + urlencode(sorted(args.items()))
    return key

def make_cache_key_lista_usuarios_visao_adm():
    args = request.args.to_dict()
    # Ordenar os parâmetros para garantir consistência na chave do cache
    key = "lista_usuarios_visao_adm_" + urlencode(sorted(args.items()))
    return key

def make_cache_key_logs():
    args = request.args.to_dict()
    # Ordenar os parâmetros para garantir consistência na chave do cache
    key = "lista_logs_" + urlencode(sorted(args.items()))
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


###
#   INVALIDACAO DE CACHE
###

# Legal de fazer mas não será utilizado pois a lógica mais simples é definir um timeout de 5 minutos
def invalidar_cache_lista_logs(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Se ainda não invalidamos o cache nesta requisição, invalidamos agora
        if not getattr(g, 'log_limpo', False):
            invalidar_cache('*lista_logs_*')
            g.log_limpo = True  # Marca que o cache foi invalidado para esta requisição

        return func(*args, **kwargs)  # Executa a função original

    return wrapper


def invalidar_cache_perfil_usuario(id_usuario):
    global_cache.delete('perfil_usuario_' + str(id_usuario))


def invalidar_cache_home(id_usuario):
    global_cache.delete('home_current_user_' + str(id_usuario))


def invalidar_cache_usuarios():
    invalidar_cache('*lista_usuarios_*')
    invalidar_cache('*lista_usuarios_visao_adm_*')
    invalidar_cache('*perfil_usuario_*')


def invalidar_cache_lista_usuarios():
    invalidar_cache('*lista_usuarios_*')


def invalidar_cache_lista_usuarios_visao_adm():
    invalidar_cache('*lista_usuarios_visao_adm_*')


def invalidar_cache_lista_promessa():
    invalidar_cache('*lista_promessas_*')


def invalidar_cache(pattern):
    try:
        # Primeiro tenta Redis (preferencial)
        if hasattr(global_cache.cache, '_write_client'):
            redis_client = global_cache.cache._write_client
            
            ## Debug para ver todas as chaves existentes
            #all_keys = list(redis_client.scan_iter(match='*'))
            #current_app.logger.info(f'Todas as chaves no Redis: {[k.decode("utf-8") if isinstance(k, bytes) else k for k in all_keys]}')
            
            # Busca específica por nossas chaves
            matching_keys = list(redis_client.scan_iter(match=pattern))
            
            if matching_keys:
                pipeline = redis_client.pipeline()
                deleted_count = 0
                
                for key in matching_keys:
                    key_str = key.decode('utf-8') if isinstance(key, bytes) else key
                    current_app.logger.info(f'Deletando chave: {key_str}')
                    pipeline.delete(key)
                    deleted_count += 1
                
                pipeline.execute()
                current_app.logger.info(f'Cache Redis invalidado: {deleted_count} chaves')
                return True
            
            current_app.logger.info(f'Nenhuma chave encontrada para o padrão: {pattern}')
            
        # Fallback para SimpleCache se necessário
        elif hasattr(global_cache.cache, '_cache'):
            pattern_x = pattern.replace("*", "")
            keys_to_delete = [
                key for key in global_cache.cache._cache.keys()
                if pattern_x in key
            ]
            
            for key in keys_to_delete:
                global_cache.delete(key)
                
            current_app.logger.info(f'Cache SimpleCache invalidado: {len(keys_to_delete)} entradas')
            return True
            
        else:
            current_app.logger.error('Nenhum mecanismo de cache compatível encontrado')
            return False
            
    except Exception as e:
        current_app.logger.error(f'Erro ao invalidar cache: {str(e)}')
        return False


def invalidar_cache_geral():
    global_cache.clear()
