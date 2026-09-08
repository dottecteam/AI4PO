# Como rodar o projeto

## Pré-requisitos

- Python 3.12+
- Node.js 22+
- Docker + Docker Compose (apenas para a opção com Docker)

## Backend (pasta `api/`)

```powershell
cd api
python -m venv venv                 # só na primeira vez
venv\Scripts\activate               # só na primeira vez (ativa o ambiente)
pip install -r requirements.txt     # só na primeira vez
copy .env.example .env              # só na primeira vez
python manage.py runserver
```

Ao criar o `.env`, gere uma chave própria para o `SECRET_KEY`:

```powershell
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

> O arquivo `.env` **não** vai para o git. Cada pessoa cria o seu a partir do `.env.example`.

Backend disponível em: `http://localhost:8000`

## Frontend (pasta `web/`, em outro terminal)

```powershell
cd web
npm ci          # só na primeira vez
npm run dev
```

Frontend disponível em: `http://localhost:3000`

## Alternativa: tudo com Docker

Na raiz do projeto:

```powershell
docker compose up --build
```

## Portas

| Serviço  | Porta |
| -------- | ----- |
| Frontend | 3000  |
| Backend  | 8000  |
| Ollama   | 11434 |
