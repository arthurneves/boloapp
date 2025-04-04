import os
import mysql.connector
from mysql.connector import Error
from werkzeug.security import generate_password_hash

def create_database():
    try:
        # Conectar sem especificar o banco de dados
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD')
        )
        
        cursor = connection.cursor()
        
        # Criar banco de dados
        cursor.execute("CREATE DATABASE IF NOT EXISTS boloapp")
        print("Banco de dados 'boloapp' criado com sucesso.")
        
        # Conectar ao banco de dados
        connection.database = 'boloapp'

        # Criar tabela de squads
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS squad (
            id_squad INT AUTO_INCREMENT PRIMARY KEY,
            titulo_squad VARCHAR(100) NOT NULL,
            is_ativo BOOLEAN DEFAULT TRUE,
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            data_edicao TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
        """)
        print("Tabela 'squad' criada com sucesso.")
        
        # Criar tabela de usuários
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuario (
            id_usuario INT AUTO_INCREMENT PRIMARY KEY,
            nome_usuario VARCHAR(100) NOT NULL,
            login_usuario VARCHAR(100) UNIQUE NOT NULL,
            senha_hash VARCHAR(255) NOT NULL,
            saldo_pontos_usuario INT NOT NULL DEFAULT '0',
            id_squad INT,
            is_ativo BOOLEAN DEFAULT TRUE,
            is_administrador BOOLEAN DEFAULT FALSE,
            foto_perfil VARCHAR(255),
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            data_edicao TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (id_squad) REFERENCES squad(id_squad)
        );
        """)
        print("Tabela 'usuario' criada com sucesso.")

        # Criar tabela de categorias
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS categoria (
            id_categoria INT AUTO_INCREMENT PRIMARY KEY,
            titulo_categoria VARCHAR(100) NOT NULL,
            descricao_categoria VARCHAR(255) NOT NULL,
            is_ativo BOOLEAN DEFAULT TRUE,
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            data_edicao TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
        """)
        print("Tabela 'categoria' criada com sucesso.")

        # Criar tabela de transacao de pontos
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS transacao_pontos (
            id_transacao INT AUTO_INCREMENT PRIMARY KEY,
            id_usuario INT,
            id_categoria INT,
            pontos_transacao INT,
            descricao_transacao VARCHAR(255) NOT NULL,
            is_ativo BOOLEAN DEFAULT TRUE,
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            id_transferencia INT,
            FOREIGN KEY (id_usuario) REFERENCES usuario(id_usuario),
            FOREIGN KEY (id_categoria) REFERENCES categoria(id_categoria),
            FOREIGN KEY (id_transferencia) REFERENCES transferencia_bolos(id_transferencia)
        )
        """)
        print("Tabela 'transacao_pontos' criada com sucesso.")

        # Criar tabela de promessas
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS promessa (
            id_promessa INT AUTO_INCREMENT PRIMARY KEY,
            id_usuario INT NOT NULL,
            titulo_promessa VARCHAR(100) NOT NULL,
            descricao_promessa VARCHAR(255),
            is_ativo BOOLEAN DEFAULT TRUE,
            status_promessa INT DEFAULT 1,
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            data_edicao TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            data_cumprimento TIMESTAMP NULL,
            FOREIGN KEY (id_usuario) REFERENCES usuario(id_usuario)
        )
        """)
        print("Tabela 'promessa' criada com sucesso.")

        # Criar tabela de logs
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS log (
            id_log INT AUTO_INCREMENT PRIMARY KEY,
            id_usuario_autor INT NOT NULL,
            id_usuario_afetado INT,
            id_registro_afetado INT NOT NULL,
            tipo_entidade VARCHAR(30) NOT NULL,
            acao_log VARCHAR(50) NOT NULL,
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (id_usuario_autor) REFERENCES usuario(id_usuario)
        )
        """)
        print("Tabela 'log' criada com sucesso.")

        # Criar tabela de convites
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS convite (
            id_convite INT AUTO_INCREMENT PRIMARY KEY,
            hash_convite VARCHAR(10) UNIQUE NOT NULL,
            id_usuario_responsavel INT NOT NULL,
            id_usuario_cadastrado INT,
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            data_usuario_cadastrado TIMESTAMP,
            is_ativo BOOLEAN DEFAULT TRUE,
            FOREIGN KEY (id_usuario_responsavel) REFERENCES usuario(id_usuario),
            FOREIGN KEY (id_usuario_cadastrado) REFERENCES usuario(id_usuario)
        )
        """)
        print("Tabela 'convite' criada com sucesso.")

        # Criar tabela de regras
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS regra (
            id_regra INT AUTO_INCREMENT PRIMARY KEY,
            conteudo_regras TEXT,
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            data_edicao TIMESTAMP,
            is_ativo BOOLEAN DEFAULT TRUE
        )
        """)
        print("Tabela 'regra' criada com sucesso.")

        # Criar tabela de transferencia_bolos
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS transferencia_bolos (
            id_transferencia INT AUTO_INCREMENT PRIMARY KEY,
            usuario_origem_id INT NOT NULL,
            usuario_destino_id INT NOT NULL,
            valor INT NOT NULL,
            descricao TEXT,
            data_transferencia TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (usuario_origem_id) REFERENCES usuario(id_usuario),
            FOREIGN KEY (usuario_destino_id) REFERENCES usuario(id_usuario)
        )
        """)
        print("Tabela 'transferencia_bolos' criada com sucesso.")

        # Criar tabela de seguidores
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS seguidor (
            id_seguidor INT NOT NULL,
            id_seguido INT NOT NULL,
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (id_seguidor, id_seguido),
            FOREIGN KEY (id_seguidor) REFERENCES usuario(id_usuario),
            FOREIGN KEY (id_seguido) REFERENCES usuario(id_usuario)
        )
        """)
        print("Tabela 'seguidor' criada com sucesso.")
        
        # Criar tabela de notificações
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS notificacao (
            id_notificacao INT AUTO_INCREMENT PRIMARY KEY,
            titulo_notificacao VARCHAR(100) NOT NULL,
            corpo_notificacao TEXT NOT NULL,
            publico_alvo VARCHAR(50) NOT NULL,
            agendamento DATETIME NULL,
            id_usuario_criador INT NOT NULL,
            id_usuario_destino INT NULL,
            id_squad_destino INT NULL,
            data_envio DATETIME NULL,
            status_envio VARCHAR(20) DEFAULT 'pendente',
            total_enviados INT DEFAULT 0,
            total_falhas INT DEFAULT 0,
            is_ativo BOOLEAN DEFAULT TRUE,
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            data_edicao TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (id_usuario_criador) REFERENCES usuario(id_usuario),
            FOREIGN KEY (id_usuario_destino) REFERENCES usuario(id_usuario),
            FOREIGN KEY (id_squad_destino) REFERENCES squad(id_squad)
        )
        """)
        print("Tabela 'notificacao' criada com sucesso.")
        
        # Criar tabela de notificações enviadas
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS notificacao_enviada (
            id_notificacao INT NOT NULL,
            id_usuario INT NOT NULL,
            data_envio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (id_notificacao, id_usuario),
            FOREIGN KEY (id_notificacao) REFERENCES notificacao(id_notificacao),
            FOREIGN KEY (id_usuario) REFERENCES usuario(id_usuario)
        )
        """)
        print("Tabela 'notificacao_enviada' criada com sucesso.")
        
        # Criar tabela para push subscriptions
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS push_subscriptions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            id_usuario INT NOT NULL,
            endpoint VARCHAR(500) NOT NULL,
            p256dh TEXT NOT NULL,
            auth TEXT NOT NULL,
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            is_ativo BOOLEAN DEFAULT TRUE,
            FOREIGN KEY (id_usuario) REFERENCES usuario(id_usuario),
            UNIQUE INDEX idx_endpoint (endpoint)
        )
        """)
        print("Tabela 'push_subscriptions' criada com sucesso.")

        # Criar usuário administrador padrão
        admin_login = 'admin'
        admin_senha = generate_password_hash('admin007006')

        # Verifica se o usuário admin já existe
        cursor.execute("SELECT * FROM usuario WHERE login_usuario = %s", (admin_login,))
        existing_admin = cursor.fetchone()

        if not existing_admin:
            cursor.execute("""
            INSERT INTO usuario
            (nome_usuario, login_usuario, senha_hash, is_ativo, is_administrador)
            VALUES (%s, %s, %s, %s, %s)
            """, ('Administrador', admin_login, admin_senha, True, True))
            print("Usuário administrador criado com sucesso.")

        connection.commit()
    except Error as e:
        print(f"Erro ao criar banco de dados ou tabela: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

if __name__ == '__main__':
    create_database()
