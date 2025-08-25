# 🤖 Agno SDK Agent Generator

> **Gerador completo de agentes SDK** com interface iOS dark e backend Python para criação de agentes inteligentes integrados ao WhatsApp via Evolution API.

---

## 🌟 Visão Geral

O **Agno SDK Agent Generator** é uma plataforma completa que permite criar, configurar e implementar agentes inteligentes personalizados com interface web moderna e backend robusto. 

### ✨ Principais Funcionalidades

- 🎨 **Interface iOS Dark**: Frontend elegante com tema iOS dark, componentes nativos e microinterações
- 🤖 **Geração de Agentes**: Criação automática de código Python para agentes Agno com especialização
- 📱 **Integração WhatsApp**: Conexão direta via Evolution API com QR Code e envio de mensagens  
- 🔧 **Múltiplas Ferramentas**: Suporte para WhatsApp, Email, Calendário, Webhooks e Banco de dados
- 📊 **Sistema de Logs**: Monitoramento em tempo real com filtros e exportação
- 💾 **Persistência**: Salvamento automático de rascunhos e configurações
- 🚀 **Deploy Pronto**: Materialização no servidor e download de arquivos ZIP

---

## 🏗️ Arquitetura Completa

```
agno-sdk-agent-generator/
├── frontend/                    # Interface web iOS-like
│   ├── index.html              # Estrutura semântica completa
│   ├── styles.css              # Tema iOS dark com componentes
│   └── app.js                  # JavaScript vanilla + estado + APIs
├── backend/                     # API FastAPI robusta  
│   ├── main.py                 # Servidor principal com rotas
│   ├── schemas.py              # Validação Pydantic completa
│   ├── models.py               # Estruturas de dados internas
│   ├── services/               # Serviços especializados
│   │   ├── agno.py            # Integração framework Agno
│   │   ├── evolution.py       # Cliente Evolution API
│   │   └── generator.py       # Gerador de código com templates
│   ├── logs/                  # Arquivos de log estruturados
│   ├── requirements.txt       # Dependências otimizadas
│   └── logging.conf          # Configuração de logging
├── .env.example               # Template de configuração
└── README.md                 # Este arquivo
```

---

## 🛠️ Stack Tecnológica

### Frontend
- **HTML5 Semântico**: Estrutura acessível com ARIA
- **CSS3 Avançado**: Variáveis, Grid, Flexbox, animações iOS-like  
- **JavaScript Vanilla**: ES6+, módulos, async/await, state management

### Backend  
- **Python 3.11+**: Linguagem base moderna
- **FastAPI**: Framework web assíncrono e performático
- **Pydantic 2**: Validação e serialização de dados
- **Loguru**: Sistema de logging avançado
- **Jinja2**: Templates para geração de código
- **HTTPX**: Cliente HTTP assíncrono
- **Uvicorn**: Servidor ASGI de alta performance

### Integrações
- **Evolution API**: Integração WhatsApp completa
- **Agno Framework**: Criação e execução de agentes
- **SQLite/PostgreSQL**: Armazenamento de dados  
- **Google APIs**: Calendário e outros serviços

---

## ⚡ Instalação e Configuração

### 1. Clonagem e Preparação

```bash
# Clone o projeto
git clone <repository-url>
cd agno-sdk-agent-generator

# Crie ambiente virtual
python -m venv venv

# Ative o ambiente (Linux/Mac)
source venv/bin/activate

# Ative o ambiente (Windows)
venv\Scripts\activate
```

### 2. Backend Setup

```bash
# Instale dependências
pip install -r backend/requirements.txt

# Configure variáveis de ambiente
cp .env.example .env
# Edite .env com suas credenciais

# Crie diretório de logs
mkdir -p backend/logs

# Execute o servidor
cd backend
uvicorn main:app --reload --port 8000
```

### 3. Frontend Setup

```bash
# Navegue para frontend  
cd frontend

# Serve arquivos estáticos (opção 1)
npx live-server --port=5500

# Alternativa com http-server (opção 2)  
npx http-server -p 5500 -c-1

# Alternativa Python (opção 3)
python -m http.server 5500
```

### 4. Acesso à Aplicação

- **Frontend**: http://localhost:5500
- **Backend API**: http://localhost:8000  
- **Documentação**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/health

---

## 🔐 Configuração de Ambiente

### Variáveis Obrigatórias

```bash
# Evolution API (WhatsApp)
EVOLUTION_BASE_URL=https://api.evolution-api.com
EVOLUTION_API_KEY=your_evolution_api_key_here

# Framework Agno  
AGNO_MODEL_PROVIDER=openai
AGNO_MODEL_NAME=gpt-4o

# Configuração da Aplicação
ALLOWED_ORIGINS=http://localhost:5500
LOG_LEVEL=INFO
```

### Variáveis Opcionais

```bash
# OpenAI (para LLM)
OPENAI_API_KEY=your_openai_key_here

# Email (notificações)
SMTP_HOST=smtp.gmail.com
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password

# Segurança
API_SECRET=your_secret_key_here
```

Consulte `.env.example` para lista completa com 50+ configurações.

---

## 🎯 Fluxo de Uso Completo

### 1. Criação de Agente
1. Acesse a interface web
2. Preencha nome, especialização e instruções
3. Selecione ferramentas (WhatsApp, Email, etc.)
4. Visualize pré-visualização JSON
5. Salve rascunho ou continue

### 2. Geração de Código  
1. Clique "Gerar Código"
2. Visualize arquivos gerados (main.py, agent.py, services)
3. Copie código ou baixe ZIP
4. Materialize no servidor para execução

### 3. Integração WhatsApp
1. Crie instância Evolution API  
2. Escaneie QR Code gerado
3. Aguarde status "CONECTADO"
4. Envie mensagem de teste
5. Monitore logs em tempo real

### 4. Monitoramento
1. Acesse seção "Logs"
2. Filtre por nível (INFO, ERROR) ou origem
3. Exporte logs para análise
4. Configure alertas via webhooks

---

## 📡 API Endpoints Completos

### 🤖 Agentes

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `POST` | `/api/agents/generate` | Gera código completo do agente |
| `POST` | `/api/agents/materialize` | Salva arquivos no servidor |

### 📱 WhatsApp (Evolution)

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `POST` | `/api/wpp/instances` | Cria instância WhatsApp |
| `GET` | `/api/wpp/instances/{id}/qr` | Obtém QR Code para pareamento |
| `GET` | `/api/wpp/instances/{id}/status` | Status de conexão atual |
| `POST` | `/api/wpp/messages` | Envia mensagem de teste |

### 📊 Sistema

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `GET` | `/api/health` | Status de saúde da aplicação |
| `GET` | `/api/logs` | Consulta logs com filtros |
| `GET` | `/api/logs/stream` | Stream de logs em tempo real |

---

## 🎨 Interface e Experiência

### Tema iOS Dark
- **Cores**: Paleta oficial iOS (grafite/preto)
- **Tipografia**: SF Pro Text/Display ou system fonts
- **Componentes**: Cards 20px radius, botões pill, inputs flutuantes
- **Animações**: Transições 150-220ms, skeleton loaders
- **Acessibilidade**: Contraste AA, navegação teclado, ARIA completo

### Seções Principais
1. **Criar Agente**: Formulário completo com validação em tempo real
2. **Meus Agentes**: Grid de agentes com ações e status WhatsApp  
3. **Logs**: Console filtros com busca e exportação
4. **Configurações**: Toggles de integração e preferências

### Recursos Avançados
- 💾 **Auto-save**: Rascunhos salvos automaticamente
- 🔍 **Search**: Busca inteligente em logs e agentes
- 📱 **Responsivo**: Mobile-first design
- ♿ **Acessível**: Screen readers, high contrast, teclado
- 🎭 **Temas**: Escala de fonte e redução de movimento

---

## 🧠 Especialização de Agentes

O sistema oferece templates otimizados por especialização:

### 🎧 Atendimento ao Cliente
- Detecção de saudações e despedidas
- Escalação automática para humanos
- Base de conhecimento (FAQ)
- Histórico de conversas

### 💰 Vendas e Conversão  
- Funil de vendas automatizado
- Tratamento de objeções
- Técnicas de persuasão
- Acompanhamento de leads

### 📅 Agendamento
- Integração calendário
- Verificação de disponibilidade
- Lembretes automáticos
- Reagendamento inteligente

### 🔧 Suporte Técnico
- Diagnóstico de problemas
- Base de soluções
- Criação de tickets
- Escalação por severidade

### ⚙️ Personalizado
- Lógica totalmente customizável
- Templates flexíveis
- Integração específica

---

## 🔧 Ferramentas Disponíveis

| Ferramenta | Funcionalidades | Configuração |
|------------|----------------|--------------|
| **📱 WhatsApp** | Mensagens, mídia, grupos, QR Code | Evolution API |
| **📧 Email** | SMTP, templates, anexos | Gmail/Outlook |
| **📅 Calendário** | Google Calendar, eventos, lembretes | OAuth 2.0 |
| **🗄️ Database** | SQLite/PostgreSQL, conversas, dados | SQLAlchemy |
| **🔗 Webhooks** | APIs externas, eventos, integração | HTTP client |

---

## 📊 Monitoramento e Logs

### Sistema de Logs Estruturado
- **Níveis**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Origens**: Frontend, Backend, Evolution API, Agno
- **Formatos**: Texto estruturado, JSON para análise
- **Rotação**: 10MB por arquivo, 5 backups
- **Streaming**: Server-Sent Events para tempo real

### Métricas de Performance
- Tempo de resposta por endpoint
- Mensagens processadas por segundo  
- Uso de memória e CPU
- Status de conectividade
- Erros por categoria

---

## 🚀 Deploy e Produção

### Containerização
```bash
# Build da imagem
docker build -t agno-generator .

# Execute container
docker run -p 8000:8000 --env-file .env agno-generator
```

### Nginx Config
```nginx
server {
    listen 80;
    server_name yourdomain.com;

    # Frontend
    location / {
        root /path/to/frontend;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Variáveis de Produção
```bash
ENVIRONMENT=production
LOG_LEVEL=WARNING
ENABLE_HTTPS=true
RATE_LIMIT_PER_MINUTE=60
AUTO_BACKUP_ENABLED=true
```

---

## 🔒 Segurança

### Implementações de Segurança
- 🛡️ **CORS**: Configurado apenas para origens permitidas
- 🔐 **Rate Limiting**: 100 req/min por IP em desenvolvimento
- 🔑 **API Keys**: Todas as credenciais via variáveis de ambiente
- 🧹 **Sanitização**: Limpeza de inputs para prevenir XSS
- 📝 **Logs**: Sem vazamento de informações sensíveis
- 🔒 **Headers**: Security headers (CSP, HSTS, etc.)

### Boas Práticas  
- Secrets nunca no código fonte
- Validação rigorosa de entrada
- Timeouts em requisições externas
- Backup automático de dados
- Monitoramento de anomalias

---

## 🧪 Testes e Qualidade

### Testar Integração WhatsApp
```bash
# Teste completo da integração Evolution API
python test_integration.py

# Teste de envio de mensagem (após conectar)
python test_integration.py --send-test
```

### Executar Testes Unitários
```bash
# Testes unitários
pytest backend/tests/ -v

# Testes de integração
pytest backend/tests/integration/ -v

# Coverage
pytest --cov=backend --cov-report=html
```

### Qualidade de Código
```bash
# Formatação
black backend/

# Imports
isort backend/

# Linting  
flake8 backend/

# Type checking
mypy backend/
```

---

## 📚 Documentação Adicional

### Links Úteis
- [Documentação Agno Framework](https://docs.agno.ai)
- [Evolution API Docs](https://evolution-api.com/docs)  
- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [Pydantic V2 Guide](https://docs.pydantic.dev/2.0/)

### Contribuição
1. Fork o projeto
2. Crie branch para feature (`git checkout -b feature/amazing-feature`)
3. Commit mudanças (`git commit -m 'Add amazing feature'`)  
4. Push para branch (`git push origin feature/amazing-feature`)
5. Abra Pull Request

---

## ❓ Troubleshooting

### Problemas Comuns

**❌ "Evolution API connection failed"**
```bash
# Verifique as variáveis
echo $EVOLUTION_BASE_URL
echo $EVOLUTION_API_KEY

# Teste conexão manualmente
curl -H "Authorization: Bearer $EVOLUTION_API_KEY" $EVOLUTION_BASE_URL/instance/fetchInstances
```

**❌ "CORS error in frontend"**
- Verifique se `ALLOWED_ORIGINS` inclui `http://localhost:5500`
- Confirme se backend está rodando na porta 8000

**❌ "Module not found errors"**  
```bash
# Reinstale dependências
pip install -r requirements.txt --force-reinstall
```

**❌ "Logs não aparecem"**
- Verifique se `backend/logs/` existe
- Confirme permissões de escrita
- Ajuste `LOG_LEVEL` no .env

**❌ "WhatsApp não conecta"**
```bash
# 1. Teste a conexão com Evolution API
python test_integration.py

# 2. Verifique as credenciais no frontend (Configurações > Evolution API)
# 3. Confirme se a instância foi criada
# 4. Escaneie o QR Code gerado
# 5. Aguarde status "CONECTADO"
```

**❌ "QR Code não aparece"**
- Verifique se as credenciais da Evolution API estão corretas
- Teste a conexão na seção Configurações
- Verifique se a instância não já está conectada
- Consulte os logs do backend para detalhes

**❌ "Webhook não funciona"**
- Confirme se sua URL está acessível publicamente
- Use ngrok para túnel local em desenvolvimento
- Verifique se o endpoint `/api/wpp/webhook/{instance_id}` está funcionando
- Consulte logs para ver se eventos estão sendo recebidos

### Suporte
- 🐛 **Issues**: [GitHub Issues](https://github.com/agno/agent-generator/issues)
- 💬 **Discord**: [Agno Community](https://discord.gg/agno)
- 📧 **Email**: support@agno.ai

---

## 📝 Changelog

### v1.0.0 (2025-01-24)
- 🎉 Release inicial completo
- ✨ Interface iOS dark responsiva  
- 🤖 Geração de agentes com 5 especializações
- 📱 Integração WhatsApp via Evolution API
- 🛠️ Backend FastAPI com todos os endpoints
- 📊 Sistema de logs avançado
- 🔧 5 ferramentas integradas
- 📦 Deploy containerizado pronto

---

## 📄 Licença

MIT License © 2025 **Agno SDK Agent Generator**

Criado com ❤️ pela comunidade Agno para democratizar a criação de agentes inteligentes.

---

**🚀 Pronto para criar seu primeiro agente inteligente? [Inicie aqui!](http://localhost:5500)**