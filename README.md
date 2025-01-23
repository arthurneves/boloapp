# BoloApp

## Configuração do Ambiente

1. Crie um ambiente virtual:
```bash
python -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Configuração do Banco de Dados
- Crie um banco de dados MySQL chamado 'boloapp'
- Ajuste as configurações de conexão no arquivo `.env`

4. Iniciar a Aplicação
```bash
python run.py
```

## Executando com Docker e Redis (Cache)

1. **Certifique-se de ter o Docker e Docker Compose instalados.**

2. **Inicie os containers Docker:**
   ```bash
   docker-compose up -d
   ```
   Este comando irá iniciar os containers do banco de dados MySQL, Redis e a aplicação Flask.

3. **Acesse a aplicação:**
   A aplicação estará disponível em `http://localhost:5000`. O Redis caching estará habilitado, utilizando o Redis container para armazenar os caches.

**Observações:**

- O arquivo `docker-compose.yml` define os serviços Docker, incluindo a aplicação Flask, MySQL e Redis.
- As configurações de cache Redis são definidas no arquivo `config/config.py` e utilizadas na inicialização do Flask-Caching em `app/__init__.py`.
- Para desenvolvimento, utilize `docker-compose.dev.yml` e `docker-entrypoint.dev.sh` para hot-reloading e outras facilidades de desenvolvimento.

## Estrutura do Projeto
- `run.py`: Ponto de entrada da aplicação
- `app/`: Pacote principal da aplicação
  - `__init__.py`: Fábrica de aplicação
  - `controllers/`: Rotas e lógica de controle
  - `models/`: Modelos de dados
  - `services/`: Lógica de negócio
  - `templates/`: Templates HTML
  - `static/`: Arquivos estáticos
- `config/`: Configurações da aplicação
# boloapp
