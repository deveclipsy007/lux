# 🚀 Como Usar os Scripts do Agno SDK Agent Generator

## 📋 Guia Rápido de Inicialização

### ✅ Pré-requisitos Verificados
- ✅ **Python 3.13.1** - Instalado e funcionando
- ✅ **Node.js v24.4.1** - Instalado e funcionando
- ✅ **Scripts criados** - Prontos para uso

## 🎯 Opções de Inicialização

### 🔧 Opção 1: Primeira Execução (Recomendado)
```cmd
# Execute este comando na raiz do projeto:
start.bat
```

**O que este script faz:**
- ✅ Verifica se Python e Node.js estão instalados
- ✅ Instala dependências Python automaticamente
- ✅ Instala live-server globalmente se necessário
- ✅ Cria diretório de logs
- ✅ Inicia Backend na porta 8000
- ✅ Inicia Frontend na porta 5500
- ✅ Abre navegador automaticamente

### ⚡ Opção 2: Inicialização Rápida
```cmd
# Para uso diário (dependências já instaladas):
start-simple.bat
```

**O que este script faz:**
- 🚀 Inicia Backend rapidamente
- 🚀 Inicia Frontend rapidamente
- 🚀 Abre navegador automaticamente
- 🚀 Sem verificações (mais rápido)

### 🛑 Opção 3: Parar Serviços
```cmd
# Para parar todos os serviços:
stop.bat
```

**O que este script faz:**
- 🛑 Para processos do Backend
- 🛑 Para processos do Frontend
- 🛑 Libera portas 8000 e 5500
- 🛑 Fecha janelas relacionadas

## 🌐 URLs Importantes

Após executar qualquer script de inicialização:

| 🎯 Serviço | 🌐 URL | 📝 Descrição |
|------------|--------|---------------|
| **🎨 Frontend** | http://localhost:5500 | Interface principal do gerador |
| **⚙️ Backend** | http://localhost:8000 | API REST do sistema |
| **📚 Docs** | http://localhost:8000/docs | Documentação Swagger |
| **💚 Health** | http://localhost:8000/api/health | Status da aplicação |

## 📁 Estrutura do Projeto

```
lux/
├── 🚀 start.bat              # Script completo (primeira vez)
├── ⚡ start-simple.bat       # Script rápido (uso diário)
├── 🛑 stop.bat              # Script de parada
├── 📋 SCRIPTS.md            # Documentação detalhada
├── 📖 COMO_USAR.md          # Este guia
├── ⚙️ .env.example          # Configurações de exemplo
├── 📂 backend/
│   ├── 🐍 main.py           # Aplicação FastAPI
│   ├── 📦 requirements.txt  # Dependências Python
│   └── 📊 logs/            # Logs (criado automaticamente)
└── 📂 frontend/
    ├── 🌐 index.html        # Interface principal
    ├── ⚙️ app.js           # Lógica da aplicação
    └── 🎨 styles.css       # Estilos CSS
```

## 🔧 Configuração Inicial

### 1️⃣ Configurar Variáveis de Ambiente
```cmd
# Copie o arquivo de exemplo
copy .env.example .env

# Edite .env com suas configurações:
# - OPENAI_API_KEY=sua_chave_openai
# - EVOLUTION_API_KEY=sua_chave_evolution
# - Outras configurações necessárias
```

### 2️⃣ Primeira Execução
```cmd
# Execute o script completo
start.bat

# Aguarde a instalação automática das dependências
# O navegador abrirá automaticamente em http://localhost:5500
```

## 🎯 Fluxo de Trabalho Recomendado

### 🌅 Início do Dia
```cmd
# Navegue até a pasta do projeto
cd C:\Users\Yohann\Downloads\lux

# Execute o script rápido
start-simple.bat

# Aguarde alguns segundos e comece a trabalhar!
```

### 🌙 Final do Dia
```cmd
# Pare todos os serviços
stop.bat

# Ou simplesmente feche as janelas do terminal
```

## 🚨 Solução de Problemas

### ❌ Erro: "Porta já em uso"
```cmd
# Solução: Execute o script de parada primeiro
stop.bat

# Depois execute novamente
start.bat
```

### ❌ Erro: "Dependências não encontradas"
```cmd
# Solução: Use o script completo
start.bat

# Ele instalará automaticamente todas as dependências
```

### ❌ Erro: "Python/Node.js não encontrado"
```cmd
# Solução: Verifique se estão no PATH
python --version
node --version

# Se não funcionarem, reinstale e adicione ao PATH
```

## 🎨 Personalização

### 🔧 Alterar Portas
Edite os scripts `.bat` e altere:
- Backend: `--port 8000` para sua porta preferida
- Frontend: `--port=5500` para sua porta preferida

### 🎯 Configurações Avançadas
Edite o arquivo `.env` para:
- Configurar diferentes modelos de IA
- Alterar configurações da Evolution API
- Personalizar logs e monitoramento

## 📊 Monitoramento

### 📈 Logs em Tempo Real
- **Backend**: Janela do terminal do Backend
- **Frontend**: Janela do terminal do Frontend
- **API Logs**: http://localhost:8000/api/logs

### 🔍 Debug
- **Health Check**: http://localhost:8000/api/health
- **API Status**: Verifique se retorna `{"status": "ok"}`
- **Frontend**: Verifique se carrega corretamente

## 🎉 Pronto para Usar!

Agora você tem um ambiente completo do **Agno SDK Agent Generator** funcionando!

### 🚀 Próximos Passos:
1. ✅ Execute `start.bat` ou `start-simple.bat`
2. ✅ Acesse http://localhost:5500
3. ✅ Configure suas credenciais no `.env`
4. ✅ Comece a criar seus agentes Agno!

---

**🤖 AgnoMaster** - Framework Agno Expert  
*Performance 10,000x superior para seus agentes inteligentes* ⚡