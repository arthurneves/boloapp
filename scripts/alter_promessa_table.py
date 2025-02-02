import os
import mysql.connector
from mysql.connector import Error

def alter_table():
    try:
        # Conectar ao banco de dados
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database='boloapp'
        )
        
        cursor = connection.cursor()
        
        # Adicionar as novas colunas
        cursor.execute("""
        ALTER TABLE promessa 
        ADD COLUMN status_promessa INT DEFAULT 1,
        ADD COLUMN data_cumprimento TIMESTAMP NULL
        """)
        
        connection.commit()
        print("Tabela 'promessa' alterada com sucesso.")
        
    except Error as e:
        print(f"Erro ao alterar tabela: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

if __name__ == '__main__':
    alter_table()
