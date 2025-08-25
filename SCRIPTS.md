# 🚀 Scripts de Inicialização - Agno SDK Agent Generator

## 📋 Visão Geral

Este projeto inclui scripts batch (.bat) para facilitar a inicialização e parada dos serviços do **Agno SDK Agent Generator** no Windows.

## 📁 Scripts Disponíveis

### 🔧 `start.bat` - Script Completo
**Recomendado para primeira execução**

- ✅ Verifica dependências (Python, Node.js)
- ✅ Instala automaticamente dependências faltantes
- ✅ Cria diretórios necessários
- ✅ Inicia Backend (FastAPI + Uvicorn) na porta 8000
- ✅ Inicia Frontend (Live Server) na porta 5500
- ✅ Abre navegador automaticamente
- ✅ Validações completas de ambiente

```bash
# Execute na raiz do projeto
.\start.bat
```

### ⚡ `start-simple.bat` - Script Rápido
**Para uso diário (dependências já instaladas)**

- 🚀 Inicialização rápida sem verificações
- 🚀 Assume que dependências estão instaladas
- 🚀 Ideal para desenvolvimento contínuo

```bash
# Execute na raiz do projeto
.\start-simple.bat
```

### 🛑 `stop.bat` - Script de Parada
**Para parar todos os serviços**

- 🛑 Para processos do Backend (uvicorn)
- 🛑 Para processos do Frontend (live-server)
- 🛑 Libera portas 8000 e 5500
- 🛑 Finaliza janelas de terminal relacionadas

```bash
# Execute de qualquer local
.\stop.bat
```

## 🌐 URLs de Acesso

Após executar os scripts de inicialização:

| Serviço | URL | Descrição |
|---------|-----|-----------|
| **Frontend** | http://localhost:5500 | Interface principal do gerador |
| **Backend API** | http://localhost:8000 | API REST do backend |
| **Documentação** | http://localhost:8000/docs | Swagger UI da API |
| **Health Check** | http://localhost:8000/api/health | Status da aplicação |

## 📋 Pré-requisitos

### Obrigatórios
- **Python 3.8+** instalado e no PATH
- **Node.js 16+** instalado e no PATH
- **npm** disponível globalmente

### Dependências Python
```bash
# Instaladas automaticamente pelo start.bat
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.5.0
# ... outras dependências em backend/requirements.txt
```

### Dependências Node.js
```bash
# Instalada automaticamente pelo start.bat
npm install -g live-server
```

## 🔧 Configuração

### 1. Variáveis de Ambiente
```bash
# Copie o arquivo de exemplo
copy .env.example .env

# Edite .env com suas configurações
# - Evolution API credentials
# - OpenAI API key
# - Outras configurações específicas
```

### 2. Estrutura de Diretórios
```
lux/
├── start.bat              # Script completo
├── start-simple.bat       # Script rápido
├── stop.bat              # Script de parada
├── .env.example          # Exemplo de configuração
├── backend/
│   ├── main.py           # Aplicação FastAPI
│   ├── requirements.txt  # Dependências Python
│   └── logs/            # Logs da aplicação (criado automaticamente)
└── frontend/
    ├── index.html        # Interface principal
    ├── app.js           # Lógica da aplicação
    └── styles.css       # Estilos CSS
```

## 🚨 Solução de Problemas

### Erro: "Python não encontrado"
```bash
# Instale Python 3.8+ e adicione ao PATH
# Verifique: python --version
```

### Erro: "Node.js não encontrado"
```bash
# Instale Node.js 16+ e adicione ao PATH
# Verifique: node --version
```

### Erro: "Porta já em uso"
```bash
# Execute o script de parada primeiro
.\stop.bat

# Depois execute novamente
.\start.bat
```

### Erro: "Dependências não instaladas"
```bash
# Use o script completo que instala automaticamente
.\start.bat

# Ou instale manualmente:
cd backend
pip install -r requirements.txt
npm install -g live-server
```

## 🔄 Fluxo de Desenvolvimento

### Primeira Execução
1. Clone/baixe o projeto
2. Configure `.env` (copie de `.env.example`)
3. Execute `start.bat`
4. Aguarde instalação automática das dependências
5. Acesse http://localhost:5500

### Uso Diário
1. Execute `start-simple.bat`
2. Desenvolva normalmente
3. Execute `stop.bat` quando terminar

### Deploy/Produção
- Use Docker com `docker-compose.yml`
- Configure variáveis de ambiente de produção
- Use proxy reverso (nginx) para SSL

## 📊 Monitoramento

### Logs do Backend
- **Localização**: `backend/logs/`
- **Formato**: JSON estruturado
- **Níveis**: DEBUG, INFO, WARNING, ERROR

### Logs em Tempo Real
- **Endpoint**: http://localhost:8000/api/logs/stream
- **Formato**: Server-Sent Events
- **Autenticação**: Bearer token necessário

## 🛡️ Segurança

### Desenvolvimento
- CORS configurado para localhost
- API key de desenvolvimento padrão
- Logs detalhados habilitados

### Produção
- Configure `API_SECRET` forte no `.env`
- Use HTTPS com certificados válidos
- Configure CORS para domínios específicos
- Desabilite logs de DEBUG

## 📚 Recursos Adicionais

- **Documentação Agno**: https://docs.agno.ai
- **Evolution API**: https://evolution-api.com
- **FastAPI Docs**: https://fastapi.tiangolo.com
- **Live Server**: https://www.npmjs.com/package/live-server

---

**AgnoMaster** - Especialista em Framework Agno  
*Criando agentes inteligentes com performance 10,000x superior* 🚀