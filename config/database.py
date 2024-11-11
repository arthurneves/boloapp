import mysql.connector
from mysql.connector import Error

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
            is_ativo BOOLEAN DEFAULT TRUE,
            is_administrador BOOLEAN DEFAULT FALSE,
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            data_edicao TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
        """)
        print("Tabela 'usuario' criada com sucesso.")
        
        connection.commit()
    except Error as e:
        print(f"Erro ao criar banco de dados ou tabela: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

if __name__ == '__main__':
    create_database()
