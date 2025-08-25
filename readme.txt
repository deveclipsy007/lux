# Agno SDK Agent Generator

> Um **gerador de agentes SDK** com frontend no estilo iOS dark (HTML, CSS e JS vanilla) e backend em **FastAPI + Agno Framework**, integrando ao **WhatsApp via Evolution API**.

---

## ✨ Visão Geral
O projeto **Agno SDK Agent Generator** permite que desenvolvedores criem agentes personalizados, exportem o código Python (usando o framework [Agno](https://docs.agno.ai)) e conectem diretamente ao WhatsApp via [Evolution API](https://evolution-api.com/).

### Funcionalidades principais
- Criar agente com **nome, instruções, especialização e integrações**.
- Gerar automaticamente código Python (SDK Agno).
- Baixar ou materializar no servidor (`main.py`, `agent.py`, `services/evolution.py`).
- Conectar ao WhatsApp via Evolution API (instância, QR Code, status, envio de mensagens).
- Logs acessíveis via endpoint protegido e arquivo local.

---

## 📂 Estrutura do Projeto

```bash
agno-agent-generator/
├── frontend/
│   ├── index.html
│   ├── styles.css
│   └── app.js
├── backend/
│   ├── main.py
│   ├── schemas.py
│   ├── models.py
│   ├── services/
│   │   ├── agno.py
│   │   ├── evolution.py
│   │   └── generator.py
│   ├── logging.conf
│   ├── requirements.txt
├── backend/logs/
├── .env.example
└── README.md
```

---

## 🛠️ Stack Tecnológica
- **Frontend**: HTML5, CSS3, JavaScript vanilla.
- **Backend**: Python 3.11+, FastAPI, Uvicorn.
- **Agno Framework**: criação/execução de agentes.
- **Evolution API**: integração WhatsApp (instâncias, QR, mensagens).
- **Outros**: `httpx`, `pydantic`, `loguru`, `python-dotenv`.

---

## 🔑 Variáveis de Ambiente

Arquivo `.env`:
```bash
EVOLUTION_BASE_URL=https://api.evolution-api.com
EVOLUTION_API_KEY=your_api_key_here
EVOLUTION_DEFAULT_INSTANCE=agno-agent
AGNO_MODEL_PROVIDER=openai
AGNO_MODEL_NAME=gpt-4o
ALLOWED_ORIGINS=http://localhost:5500
LOG_LEVEL=DEBUG
```

---

## 🚀 Como Rodar

### 1. Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows

pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### 2. Frontend
```bash
cd frontend
# usar live-server ou http-server
npx live-server
```

Acesse: [http://localhost:5500](http://localhost:5500)

---

## 🔗 Fluxo do Usuário

```mermaid
flowchart TD
    A[Início: Criar Agente] --> B[Gerar Código SDK Agno]
    B --> C[Materializar/Download ZIP]
    C --> D[Integração WhatsApp]
    D --> E[Exibir QR Code]
    E --> F[Conectar Instância]
    F --> G[Enviar Mensagem Teste]
    G --> H[Logs em tempo real]
```

---

## 📡 Endpoints Principais

### Agentes
- `POST /api/agents/generate` → Gera arquivos do agente.
- `POST /api/agents/materialize` → Salva arquivos no servidor.

### Evolution API (WhatsApp)
- `POST /api/wpp/instances` → Cria/recupera instância.
- `GET /api/wpp/instances/{id}/qr` → Retorna QR Code.
- `GET /api/wpp/instances/{id}/status` → Status de conexão.
- `POST /api/wpp/messages` → Envia mensagem teste.

### Logs
- `GET /api/logs` → Consulta streaming de logs.

---

## 📖 Documentação
- [Agno Framework Docs](https://docs.agno.ai)
- [Evolution API Docs](https://evolution-api.com/docs)

---

## ✅ Critérios de Aceite
- UI com estética iOS dark.
- Validação completa de formulários.
- Geração de código Python com Agno.
- Integração WhatsApp funcional (QR + envio de mensagens).
- Logs acessíveis via API e arquivo local.

---

## 🧩 Próximos Passos (Stretch Goals)
- Webhook para mensagens recebidas.
- Console em tempo real para conversas.
- Templates pré-prontos de especialização.

---

## 📜 Licença
MIT © 2025 Gambit Group
