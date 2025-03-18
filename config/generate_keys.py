from pywebpush import webpush, WebPushException
import base64
import os
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization

def generate_vapid_keys():
    """
    Gera um par de chaves VAPID no formato correto para pywebpush
    """
    # Gerar par de chaves ECDSA
    private_key = ec.generate_private_key(ec.SECP256R1())
    public_key = private_key.public_key()
    
    # Serializar chave privada para o formato correto
    private_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    # Serializar chave pública para o formato correto
    public_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint
    )
    
    # Converter para base64url (sem padding)
    private_key_base64 = base64.urlsafe_b64encode(private_bytes).decode('utf-8').rstrip('=')
    public_key_base64 = base64.urlsafe_b64encode(public_bytes).decode('utf-8').rstrip('=')
    
    return {
        'private_key': private_key_base64,
        'public_key': public_key_base64
    }

def main():
    # Gerar chaves VAPID
    keys = generate_vapid_keys()
    
    # Criar arquivo .env se não existir
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    
    # Verificar se já existem as variáveis no .env
    existing_env = {}
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                if '=' in line:
                    key, value = line.strip().split('=', 1)
                    existing_env[key] = value

    # Adicionar ou atualizar as variáveis VAPID
    existing_env['VAPID_PRIVATE_KEY'] = keys['private_key']
    existing_env['VAPID_PUBLIC_KEY'] = keys['public_key']
    if 'VAPID_CLAIM_EMAIL' not in existing_env:
        existing_env['VAPID_CLAIM_EMAIL'] = 'admin@example.com'  # Email padrão, você deve alterar depois

    # Salvar no arquivo .env
    with open(env_path, 'w') as f:
        for key, value in existing_env.items():
            f.write(f'{key}={value}\n')

    print("\nChaves VAPID geradas com sucesso!")
    print("\nAs seguintes variáveis foram adicionadas/atualizadas no arquivo .env:")
    print(f"VAPID_PRIVATE_KEY={keys['private_key']}")
    print(f"VAPID_PUBLIC_KEY={keys['public_key']}")
    print("\nIMPORTANTE:")
    print("1. Certifique-se de atualizar VAPID_CLAIM_EMAIL no arquivo .env com seu email real")
    print("2. Atualize o vapidPublicKey em app/static/js/notification-handler.js com a chave pública acima")
    print("3. Reinicie o servidor Flask para aplicar as alterações")

if __name__ == "__main__":
    main()
