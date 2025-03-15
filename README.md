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

## Funcionalidades da Aplicação

A aplicação BoloApp possui as seguintes funcionalidades, organizadas por página:

- **Página Inicial (Home):**
    - Dashboard com informações gerais e gráficos analíticos.
- **Usuários:**
    - Listagem de usuários (administrativo): Permite visualizar e gerenciar todos os usuários do sistema para administradores.
    - Listagem de usuários (comum): Permite que usuários comuns vejam outros usuários.
    - Criação de novo usuário (administrativo): Funcionalidade administrativa para criar novas contas de usuário.
    - Criação de novo usuário via convite: Permite o cadastro de novos usuários através de convites gerados por administradores.
    - Edição de usuário: Permite modificar informações de usuários existentes.
    - Perfil do usuário: Exibe informações detalhadas sobre o perfil de um usuário específico.
    - Login de usuário: Permite que usuários autenticados acessem o sistema.
- **Categorias:**
    - Listagem de categorias: Exibe as categorias de transações de pontos cadastradas.
    - Criação de nova categoria: Permite adicionar novas categorias para classificar transações de pontos.
    - Edição de categoria: Permite modificar categorias existentes.
- **Promessas:**
    - Listagem de promessas: Exibe uma lista de promessas com funcionalidades de filtro e paginação.
    - Criação de nova promessa: Permite registrar novas promessas.
    - Edição de promessa: Permite modificar detalhes de promessas existentes.
    - Desativação de promessa: Permite inativar promessas.
    - Reativação de promessa: Permite ativar promessas previamente desativadas.
    - Cumprir promessa: Permite marcar promessas como cumpridas.
- **Squads:**
    - Listagem de squads (administrativo): Exibe os squads existentes para gerenciamento administrativo.
    - Criação de novo squad (administrativo): Permite criar novos squads para organizar usuários.
    - Edição de squad (administrativo): Permite modificar informações de squads existentes.
    - Desativação de squad (administrativo): Permite inativar squads.
- **Transações de Pontos:**
    - Listagem de transações de pontos: Exibe transações de pontos com opções de filtro e paginação.
    - Criação de nova transação de pontos: Permite registrar novas transações de pontos.
    - Edição de transação de pontos: Permite modificar transações de pontos existentes.
    - Desativação de transação de pontos: Permite inativar transações de pontos.
    - Reativação de transação de pontos: Permite ativar transações de pontos desativadas.
    - Transferência de pontos entre usuários: Funcionalidade para transferir pontos entre usuários.
- **Convites:**
    - Criação de convite (administrativo): Permite gerar convites para novos usuários se cadastrarem.
    - Cadastro de usuário via convite (público com hash): Permite que novos usuários se cadastrem usando um hash de convite.
- **Regras:**
    - Visualização da regra ativa: Exibe a regra de pontos atualmente ativa no sistema.
    - Edição da regra ativa: Permite modificar a regra de pontos ativa.
    - Listagem de versões de regras: Exibe um histórico das versões das regras de pontos.
    - Visualização de versão específica de regra: Permite visualizar detalhes de uma versão específica da regra.
    - Ativação de versão específica de regra: Permite ativar uma versão específica da regra, tornando-a a regra vigente.
- **Logs:**
    - Listagem de logs (administrativo): Exibe logs de atividades do sistema para auditoria e monitoramento administrativo, com filtros e paginação.

# boloapp
