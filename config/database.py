import mysql.connector
from mysql.connector import Error
from werkzeug.security import generate_password_hash

def create_database():
    try:
        # Conectar sem especificar o banco de dados
        connection = mysql.connector.connect(
            host='localhost',
            user='admin',
            password=''
        )
        
        cursor = connection.cursor()
        
        # Criar banco de dados
        cursor.execute("CREATE DATABASE IF NOT EXISTS boloapp")
        print("Banco de dados 'boloapp' criado com sucesso.")
        
        # Conectar ao banco de dados
        connection.database = 'boloapp'
        
        # Criar tabela de usuários
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuario (
            id_usuario INT AUTO_INCREMENT PRIMARY KEY,
            nome_usuario VARCHAR(100) NOT NULL,
            email_usuario VARCHAR(100) UNIQUE NOT NULL,
            senha_hash VARCHAR(255) NOT NULL,
            is_ativo BOOLEAN DEFAULT TRUE,
            is_administrador BOOLEAN DEFAULT FALSE,
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            data_edicao TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
        """)
        print("Tabela 'usuario' criada com sucesso.")


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

        # Alterar tabela de usuários para adicionar relacionamento com squad
        cursor.execute("""
        ALTER TABLE usuario 
        ADD COLUMN id_squad INT,
        ADD FOREIGN KEY (id_squad) REFERENCES squad(id_squad)
        """)
        print("Coluna id_squad adicionada à tabela de usuários.")

        
        # Criar usuário administrador padrão
        admin_email = 'admin@email.com'
        admin_senha = generate_password_hash('admin007006')
        
        # Verifica se o usuário admin já existe
        cursor.execute("SELECT * FROM usuario WHERE email_usuario = %s", (admin_email,))
        existing_admin = cursor.fetchone()
        
        if not existing_admin:
            cursor.execute("""
            INSERT INTO usuario 
            (nome_usuario, email_usuario, senha_hash, is_ativo, is_administrador) 
            VALUES (%s, %s, %s, %s, %s)
            """, ('Administrador', admin_email, admin_senha, True, True))
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
