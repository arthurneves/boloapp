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
