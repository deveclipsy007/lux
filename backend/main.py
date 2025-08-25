#!/usr/bin/env python3
"""
Agno SDK Agent Generator - Backend API

Aplicação FastAPI para geração de agentes SDK com integração ao WhatsApp
via Evolution API.

Funcionalidades:
- Geração de código Python para agentes Agno
- Integração com Evolution API (WhatsApp)
- Sistema de logs estruturado
- Endpoints para criação e materialização de agentes

Autor: Agno SDK Agent Generator
Data: 2025-01-24
"""

import os
import sys
import json
import asyncio
import uuid
from contextlib import asynccontextmanager
from typing import List, Dict, Any, Optional
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException, Depends, status, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings
from loguru import logger

# Importa módulos locais
from schemas import (
    AgentCreate,
    AgentGeneratedFiles,
    WppInstance,
    SendMessage,
    HealthResponse,
    LogEntry,
    MaterializeRequest,
    AgentInfo,
    AgentUpdate,
)
from services.generator import CodeGeneratorService
from services.evolution import EvolutionService
from services.agno import AgnoService
from models import AgentRepository, SystemEvent, EventType, app_store

# WebSocket imports (bypassing problematic modules)
try:
    # Import directly to avoid __init__.py issues
    import sys
    from pathlib import Path
    websocket_path = Path(__file__).parent / "websocket"
    sys.path.insert(0, str(websocket_path))
    
    from websocket_manager import WebSocketManager
    from websocket_auth import WebSocketAuthenticator
    websocket_available = True
    logger.info("WebSocket modules loaded successfully")
except ImportError as e:
    logger.warning(f"WebSocket modules not available: {e}")
    websocket_available = False

# Configurações da aplicação
class Settings(BaseSettings):
    """Configurações da aplicação carregadas de variáveis de ambiente"""
    
    # Evolution API
    evolution_base_url: str = "https://api.evolution-api.com"
    evolution_api_key: str = ""
    evolution_default_instance: str = "agno-agent"
    
    # Agno
    agno_model_provider: str = "openai" 
    agno_model_name: str = "gpt-4o"
    
    # Aplicação
    allowed_origins: str = "http://localhost:5500,http://localhost:3000,http://127.0.0.1:5500"
    log_level: str = "DEBUG"
    
    # Segurança
    api_secret: str = "dev-secret-key"  # Em produção usar variável de ambiente
    
    # Paths
    logs_dir: Path = Path("logs")
    generated_agents_dir: Path = Path("generated_agents")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Allow extra fields in .env

# Instância global das configurações
settings = Settings()

# Repositório de agentes com persistência simples em disco
agent_repo = AgentRepository(Path("agents.json"))

# Caminho para persistência de eventos do sistema
events_file = settings.logs_dir / "events.json"


async def log_event(event_type: EventType, agent_id: str, data: Dict[str, Any]) -> None:
    """Registra evento do sistema em memória e em arquivo."""
    event = SystemEvent(
        id="",
        event_type=event_type,
        target_id=agent_id,
        data=data,
        source="backend",
    )

    # Armazena em memória
    await app_store.add_event(event)

    # Persiste em arquivo
    try:
        events_file.parent.mkdir(exist_ok=True)
        existing = (
            json.loads(events_file.read_text(encoding="utf-8"))
            if events_file.exists()
            else []
        )
        existing.append(event.to_dict())
        events_file.write_text(
            json.dumps(existing, indent=2, ensure_ascii=False), encoding="utf-8"
        )
    except Exception as e:
        logger.error(f"Erro ao registrar evento: {e}")

# Configuração de logging
def setup_logging():
    """Configura sistema de logs estruturado"""
    
    # Remove handlers padrão do loguru
    logger.remove()
    
    # Cria diretório de logs se não existir
    settings.logs_dir.mkdir(exist_ok=True)
    
    # Console handler
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=settings.log_level,
        colorize=True
    )
    
    # Arquivo handler - Todos os logs
    logger.add(
        settings.logs_dir / "app.log",
        rotation="10 MB",
        retention="7 days",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        serialize=False
    )
    
    # Arquivo handler - Apenas erros
    logger.add(
        settings.logs_dir / "errors.log", 
        rotation="10 MB",
        retention="30 days",
        level="ERROR",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        serialize=False
    )
    
    logger.info("Sistema de logging configurado")

# Lifecycle da aplicação
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia ciclo de vida da aplicação"""
    
    # Startup
    logger.info("🚀 Iniciando Agno SDK Agent Generator Backend")
    
    # Cria diretórios necessários
    settings.generated_agents_dir.mkdir(exist_ok=True)
    logger.info(f"Diretório de agentes criado: {settings.generated_agents_dir}")

    # Carrega agentes persistidos
    agent_repo.load()
    logger.info(f"{len(agent_repo.list_agents())} agentes carregados do disco")
    
    # Testa conectividade com serviços externos
    try:
        evolution_service = EvolutionService(settings)
        await evolution_service.test_connection()
        logger.info("✅ Conexão com Evolution API testada")
    except Exception as e:
        logger.warning(f"⚠️  Erro ao conectar com Evolution API: {e}")
    
    logger.info("🟢 Aplicação pronta para receber requisições")

    yield

    # Shutdown
    agent_repo.save()
    logger.info("🔴 Finalizando aplicação...")

# Criação da aplicação FastAPI
app = FastAPI(
    title="Agno SDK Agent Generator API",
    description="API para geração de agentes SDK com integração ao WhatsApp via Evolution API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configuração CORS
allowed_origins = settings.allowed_origins.split(",") if settings.allowed_origins else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Segurança (Bearer token simples para desenvolvimento)
security = HTTPBearer(auto_error=False)

async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    """Validação simples de token para endpoints protegidos"""

    if not credentials or credentials.credentials != settings.api_secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de acesso inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {"user": "authenticated", "scope": "admin"}

# Inicialização de serviços
generator_service = CodeGeneratorService(settings)
agno_service = AgnoService(settings)

def get_evolution_service() -> EvolutionService:
    """Dependency injection para EvolutionService"""
    return EvolutionService(settings)

# Middleware para logging de requisições
@app.middleware("http")
async def log_requests(request, call_next):
    """Middleware para logging automático de requisições"""
    
    start_time = asyncio.get_event_loop().time()
    
    # Log da requisição
    logger.info(f"📥 {request.method} {request.url.path} - {request.client.host}")
    
    try:
        response = await call_next(request)
        
        # Log da resposta
        process_time = asyncio.get_event_loop().time() - start_time
        logger.info(f"📤 {response.status_code} {request.url.path} - {process_time:.3f}s")
        
        return response
        
    except Exception as e:
        process_time = asyncio.get_event_loop().time() - start_time
        logger.error(f"❌ Error {request.url.path} - {process_time:.3f}s: {str(e)}")
        raise

# ENDPOINTS DA API

@app.get("/", response_model=HealthResponse)
async def root():
    """Endpoint raiz com informações da API"""
    return HealthResponse(
        status="healthy",
        message="Agno SDK Agent Generator API is running",
        version="1.0.0",
        timestamp=asyncio.get_event_loop().time()
    )

@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    try:
        # Testa conectividade básica
        return HealthResponse(
            status="healthy",
            message="All systems operational",
            version="1.0.0",
            timestamp=asyncio.get_event_loop().time()
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service temporarily unavailable"
        )

# CRUD de agentes


@app.get("/api/agents", response_model=List[AgentInfo])
async def list_agents(current_user: Dict = Depends(get_current_user)):
    """Lista todos os agentes cadastrados."""
    return [agent.to_dict() for agent in agent_repo.list_agents()]


@app.get("/api/agents/{agent_id}", response_model=AgentInfo)
async def get_agent(agent_id: str, current_user: Dict = Depends(get_current_user)):
    """Retorna um agente específico."""
    agent = agent_repo.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agente não encontrado")
    return agent.to_dict()


@app.post("/api/agents", response_model=AgentInfo, status_code=status.HTTP_201_CREATED)
async def create_agent(agent_in: AgentCreate, current_user: Dict = Depends(get_current_user)):
    """Cria um novo agente."""
    data = {
        "name": agent_in.agent_name,
        "specialization": agent_in.specialization,
        "instructions": agent_in.instructions,
        "tools": agent_in.tools,
    }
    if agent_in.integrations:
        data["config"] = {
            "integrations": agent_in.integrations.dict(exclude_none=True)
        }
    agent = agent_repo.create_agent(data)
    await log_event(EventType.AGENT_CREATED, agent.id, agent.to_dict())
    return agent.to_dict()


@app.put("/api/agents/{agent_id}", response_model=AgentInfo)
async def update_agent(agent_id: str, agent_in: AgentUpdate, current_user: Dict = Depends(get_current_user)):
    """Atualiza um agente existente."""
    update_data = {
        k: v
        for k, v in {
            "name": agent_in.agent_name,
            "specialization": agent_in.specialization,
            "instructions": agent_in.instructions,
            "tools": agent_in.tools,
        }.items()
        if v is not None
    }
    if agent_in.integrations is not None:
        update_data["config"] = {
            "integrations": agent_in.integrations.dict(exclude_none=True)
        }
    agent = agent_repo.update_agent(agent_id, update_data)
    if not agent:
        raise HTTPException(status_code=404, detail="Agente não encontrado")
    await log_event(EventType.AGENT_UPDATED, agent_id, agent.to_dict())
    return agent.to_dict()


@app.delete("/api/agents/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    agent_id: str,
    evolution_service: EvolutionService = Depends(get_evolution_service),
    current_user: Dict = Depends(get_current_user),
):
    """Remove um agente e sua instância associada no Evolution API."""

    agent = agent_repo.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agente não encontrado")

    # Determina o nome da instância do WhatsApp associada
    instance_name: Optional[str] = None

    try:
        instance_name = (
            agent.config.get("evolution_instance_name")
            or agent.config.get("instance_name")
            or agent.config.get("whatsapp", {}).get("instance_name")
        )
    except Exception:
        instance_name = None

    if not instance_name:
        # Tenta inferir pelo padrão de nome
        possible = f"{agent.name}-whatsapp"
        if evolution_service.get_cached_instance(possible):
            instance_name = possible

    if instance_name:
        try:
            success = await evolution_service.delete_instance(instance_name)
            if not success:
                logger.error(
                    f"Falha ao excluir instância {instance_name} do agente {agent.name}"
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Erro ao excluir instância do WhatsApp",
                )
            logger.info(
                f"Instância {instance_name} do agente {agent.name} excluída com sucesso"
            )
        except Exception as e:
            logger.error(
                f"Erro ao excluir instância {instance_name} do agente {agent.name}: {e}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erro ao excluir instância do WhatsApp: {e}",
            )
    else:
        logger.warning(
            f"Nenhuma instância associada encontrada para o agente {agent.name}"
        )

    if not agent_repo.delete_agent(agent_id):
        raise HTTPException(status_code=404, detail="Agente não encontrado")
    await log_event(EventType.AGENT_DELETED, agent_id, {"name": agent.name})
    logger.info(f"Agente {agent.name} removido com sucesso")
    return JSONResponse(status_code=status.HTTP_204_NO_CONTENT, content=None)

# ENDPOINTS DE AUDITORIA

@app.get("/api/events", response_model=List[Dict[str, Any]])
async def get_events(current_user: Dict = Depends(get_current_user)):
    """Retorna eventos do sistema para auditoria."""
    if events_file.exists():
        return json.loads(events_file.read_text(encoding="utf-8"))
    return []

# ENDPOINTS DE AGENTES

@app.post("/api/agents/generate", response_model=AgentGeneratedFiles)
async def generate_agent(
    agent_data: AgentCreate,
    background_tasks: BackgroundTasks
):
    """
    Gera arquivos de código Python para um agente baseado nas especificações
    
    Args:
        agent_data: Dados do agente (nome, instruções, especialização, tools)
        
    Returns:
        AgentGeneratedFiles: Lista de arquivos gerados com path e conteúdo
    """
    
    logger.info(f"🤖 Gerando agente: {agent_data.agent_name}")
    
    try:
        # Valida dados de entrada
        if not agent_data.agent_name.replace('-', '').replace('_', '').isalnum():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Nome do agente deve conter apenas letras, números, hífen e underscore"
            )
        
        if len(agent_data.instructions) < 80:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Instruções devem ter pelo menos 80 caracteres"
            )
        
        # Gera arquivos do agente
        generated_files = await generator_service.generate_agent_files(agent_data)
        
        # Log da geração bem-sucedida
        background_tasks.add_task(
            lambda: logger.info(f"✅ Agente {agent_data.agent_name} gerado com sucesso - {len(generated_files.files)} arquivos")
        )
        
        return generated_files
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao gerar agente {agent_data.agent_name}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno ao gerar agente: {str(e)}"
        )

@app.post("/api/agents/materialize")
async def materialize_agent(
    request: MaterializeRequest,
    background_tasks: BackgroundTasks
):
    """
    Materializa (salva) os arquivos gerados no sistema de arquivos do servidor
    
    Args:
        request: Dados do agente e arquivos gerados
        
    Returns:
        Confirmação de sucesso
    """
    
    logger.info(f"💾 Materializando agente: {request.agent_name}")
    
    try:
        # Cria diretório do agente
        agent_dir = settings.generated_agents_dir / request.agent_name
        agent_dir.mkdir(exist_ok=True)
        
        # Salva cada arquivo
        saved_files = []
        for file_data in request.files:
            file_path = agent_dir / file_data["path"].replace("backend/", "")
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(file_data["content"])
            
            saved_files.append(str(file_path))
            logger.debug(f"📄 Arquivo salvo: {file_path}")
        
        # Log da materialização bem-sucedida
        background_tasks.add_task(
            lambda: logger.info(f"✅ Agente {request.agent_name} materializado - {len(saved_files)} arquivos salvos")
        )
        
        return {
            "ok": True,
            "message": f"Agente {request.agent_name} materializado com sucesso",
            "files_saved": len(saved_files),
            "agent_directory": str(agent_dir)
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao materializar agente {request.agent_name}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao salvar agente: {str(e)}"
        )

# ENDPOINTS DE WHATSAPP (EVOLUTION API)

@app.post("/api/wpp/instances", response_model=WppInstance)
async def create_whatsapp_instance(
    instance_data: Dict[str, str],
    evolution_service: EvolutionService = Depends(get_evolution_service)
):
    """
    Cria ou recupera uma instância do WhatsApp via Evolution API
    
    Args:
        instance_data: Dados da instância (ex: {"instance_name": "my-agent"})
        
    Returns:
        WppInstance: Dados da instância criada
    """
    
    instance_name = instance_data.get("instance_name", settings.evolution_default_instance)
    logger.info(f"📱 Criando instância WhatsApp: {instance_name}")
    
    try:
        result = await evolution_service.create_instance(instance_name)
        
        logger.info(f"✅ Instância {instance_name} criada/recuperada")
        
        return WppInstance(
            instance_id=instance_name,
            status=result.get("status", "UNKNOWN"),
            qr_code=result.get("qr_code"),
            webhook_url=result.get("webhook_url")
        )
        
    except Exception as e:
        logger.error(f"❌ Erro ao criar instância {instance_name}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao criar instância WhatsApp: {str(e)}"
        )

@app.get("/api/wpp/instances/{instance_id}/qr")
async def get_qr_code(
    instance_id: str,
    evolution_service: EvolutionService = Depends(get_evolution_service)
):
    """
    Obtém o QR Code para pareamento da instância
    
    Args:
        instance_id: ID da instância
        
    Returns:
        QR Code em base64 e status da instância
    """
    
    logger.info(f"📱 Obtendo QR Code para: {instance_id}")
    
    try:
        result = await evolution_service.get_qr_code(instance_id)
        
        if not result or not result.get("qr"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="QR Code não disponível ou instância não encontrada"
            )
        
        logger.info(f"✅ QR Code obtido para {instance_id}")
        
        return {
            "qr": result["qr"],
            "status": result.get("status", "QR_AVAILABLE"),
            "expires_at": result.get("expires_at")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao obter QR Code {instance_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao obter QR Code: {str(e)}"
        )

@app.get("/api/wpp/instances/{instance_id}/status", response_model=WppInstance)
async def get_instance_status(
    instance_id: str,
    evolution_service: EvolutionService = Depends(get_evolution_service)
):
    """
    Consulta o status de conexão de uma instância
    
    Args:
        instance_id: ID da instância
        
    Returns:
        WppInstance: Status atual da instância
    """
    
    logger.debug(f"📊 Consultando status da instância: {instance_id}")
    
    try:
        status_info = await evolution_service.get_instance_status(instance_id)
        
        return WppInstance(
            instance_id=instance_id,
            status=status_info.get("state", "UNKNOWN"),
            phone_number=status_info.get("phone_number"),
            profile_name=status_info.get("profile_name")
        )
        
    except Exception as e:
        logger.error(f"❌ Erro ao consultar status {instance_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao consultar status: {str(e)}"
        )

@app.post("/api/wpp/instances/{instance_id}/webhook")
async def set_instance_webhook(
    instance_id: str,
    payload: Dict[str, Any],
    evolution_service: EvolutionService = Depends(get_evolution_service)
):
    """Configura webhook para uma instância específica"""

    logger.info(f"🔗 Configurando webhook para {instance_id}")

    try:
        webhook_url = payload.get("webhook_url")
        events = payload.get("events")

        if not webhook_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="webhook_url é obrigatório"
            )

        success = await evolution_service.set_webhook(instance_id, webhook_url, events)

        if success:
            return {"status": "success", "message": "Webhook configurado com sucesso"}

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"status": "error", "message": "Falha ao configurar webhook"}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao configurar webhook {instance_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao configurar webhook: {str(e)}"
        )

@app.post("/api/wpp/messages")
async def send_test_message(
    message_data: SendMessage,
    background_tasks: BackgroundTasks,
    evolution_service: EvolutionService = Depends(get_evolution_service)
):
    """
    Envia uma mensagem de teste via WhatsApp
    
    Args:
        message_data: Dados da mensagem (instância, destinatário, texto)
        
    Returns:
        Confirmação do envio com ID da mensagem
    """
    
    logger.info(f"💬 Enviando mensagem teste: {message_data.instance_id} -> {message_data.to}")
    
    try:
        result = await evolution_service.send_message(
            instance_id=message_data.instance_id,
            to=message_data.to,
            message=message_data.message
        )
        
        # Log assíncrono do sucesso
        background_tasks.add_task(
            lambda: logger.info(f"✅ Mensagem enviada - ID: {result.get('message_id', 'N/A')}")
        )
        
        return {
            "message_id": result.get("message_id"),
            "status": "sent",
            "timestamp": result.get("timestamp"),
            "to": message_data.to
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao enviar mensagem: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao enviar mensagem: {str(e)}"
        )

@app.post("/api/wpp/webhook/{instance_id}")
async def receive_webhook(
    instance_id: str,
    webhook_data: Dict[str, Any],
    background_tasks: BackgroundTasks,
    evolution_service: EvolutionService = Depends(get_evolution_service)
):
    """
    Webhook para receber mensagens e eventos do WhatsApp via Evolution API
    
    Args:
        instance_id: ID da instância que enviou o webhook
        webhook_data: Dados do webhook recebido
        background_tasks: Tarefas para execução em background
    """
    logger.info(f"📡 Webhook recebido da instância {instance_id}")
    
    try:
        # Registra o evento recebido
        event_type = webhook_data.get("event", "unknown")
        logger.debug(f"Evento recebido: {event_type} - Dados: {json.dumps(webhook_data, indent=2)}")
        
        # Processa diferentes tipos de eventos
        if event_type == "messages.upsert":
            # Nova mensagem recebida
            await process_incoming_message(instance_id, webhook_data, background_tasks)
            
        elif event_type == "connection.update":
            # Atualização de status de conexão
            await process_connection_update(instance_id, webhook_data)
            
        elif event_type == "qr.updated":
            # QR Code atualizado
            logger.info(f"QR Code atualizado para instância {instance_id}")
            
        else:
            logger.debug(f"Evento não processado: {event_type}")
        
        return {"status": "success", "message": "Webhook processado com sucesso"}
        
    except Exception as e:
        logger.error(f"❌ Erro ao processar webhook: {str(e)}")
        # Não levanta exceção para não quebrar o fluxo do webhook
        return {"status": "error", "message": str(e)}

async def process_incoming_message(instance_id: str, webhook_data: Dict[str, Any], background_tasks: BackgroundTasks):
    """
    Processa mensagens recebidas via webhook
    """
    try:
        messages = webhook_data.get("data", {}).get("messages", [])
        
        for message in messages:
            # Ignora mensagens próprias (fromMe = True)
            if message.get("key", {}).get("fromMe", False):
                continue
                
            from_number = message.get("key", {}).get("remoteJid", "").replace("@s.whatsapp.net", "")
            message_text = message.get("message", {}).get("conversation", "")
            message_id = message.get("key", {}).get("id", "")
            
            if not message_text:
                # Verifica outros tipos de mensagem
                extended_text = message.get("message", {}).get("extendedTextMessage", {})
                if extended_text:
                    message_text = extended_text.get("text", "")
            
            if message_text and from_number:
                logger.info(f"📨 Nova mensagem de {from_number}: {message_text[:100]}...")
                
                # Aqui seria integrado com o agente Agno para processar a mensagem
                # Por enquanto, apenas loga a mensagem recebida
                background_tasks.add_task(
                    log_received_message,
                    instance_id, from_number, message_text, message_id
                )
                
    except Exception as e:
        logger.error(f"❌ Erro ao processar mensagem recebida: {str(e)}")

async def process_connection_update(instance_id: str, webhook_data: Dict[str, Any]):
    """
    Processa atualizações de status de conexão
    """
    try:
        connection_data = webhook_data.get("data", {})
        state = connection_data.get("state", "unknown")
        
        logger.info(f"🔄 Status de conexão da instância {instance_id}: {state}")
        
        # Atualiza estado interno se necessário
        # Em uma implementação completa, isso seria salvo no banco de dados
        
    except Exception as e:
        logger.error(f"❌ Erro ao processar atualização de conexão: {str(e)}")

async def log_received_message(instance_id: str, from_number: str, message_text: str, message_id: str):
    """
    Registra mensagem recebida nos logs
    """
    logger.info(f"💬 [{instance_id}] {from_number}: {message_text}")
    
    # Em uma implementação completa, aqui seria:
    # 1. Salvos no banco de dados
    # 2. Processado pelo agente Agno
    # 3. Gerada resposta automática se configurado

# ENDPOINTS DE LOGS

@app.get("/api/logs")
async def get_logs(
    level: Optional[str] = None,
    limit: int = 100,
    current_user = Depends(get_current_user)
):
    """
    Endpoint para consulta de logs (desenvolvimento apenas)
    
    Args:
        level: Filtro por nível (DEBUG, INFO, WARNING, ERROR)
        limit: Número máximo de linhas a retornar
        
    Returns:
        Lista de entradas de log
    """
    
    try:
        log_file = settings.logs_dir / "app.log"
        
        if not log_file.exists():
            return {"logs": [], "message": "Arquivo de log não encontrado"}
        
        # Lê últimas linhas do arquivo
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Aplica filtros
        if level:
            lines = [line for line in lines if f"| {level.upper()} " in line]
        
        # Limita resultado
        lines = lines[-limit:] if limit > 0 else lines
        
        # Parseia logs para formato estruturado
        logs = []
        for line in lines[-limit:]:
            try:
                parts = line.strip().split(" | ")
                if len(parts) >= 4:
                    logs.append({
                        "timestamp": parts[0],
                        "level": parts[1].strip(),
                        "location": parts[2],
                        "message": " | ".join(parts[3:])
                    })
            except:
                # Se não conseguir parsear, adiciona linha raw
                logs.append({"raw": line.strip()})
        
        return {
            "logs": logs,
            "total": len(logs),
            "level_filter": level,
            "limit": limit
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao consultar logs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao consultar logs: {str(e)}"
        )

@app.get("/api/logs/stream")
async def stream_logs(current_user = Depends(get_current_user)):
    """
    Stream de logs em tempo real via Server-Sent Events (desenvolvimento apenas)
    
    Returns:
        StreamingResponse: Stream de eventos de log
    """
    
    async def log_stream():
        """Gerador de eventos de log"""
        
        log_file = settings.logs_dir / "app.log" 
        
        try:
            # Posição inicial no arquivo
            if log_file.exists():
                with open(log_file, 'r') as f:
                    f.seek(0, 2)  # Vai para o final
                    position = f.tell()
            else:
                position = 0
            
            while True:
                try:
                    if log_file.exists():
                        with open(log_file, 'r') as f:
                            f.seek(position)
                            new_lines = f.readlines()
                            position = f.tell()
                            
                            for line in new_lines:
                                yield f"data: {line.strip()}\n\n"
                    
                    # Pausa antes de verificar novamente
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    yield f"data: {{\"error\": \"Erro ao ler logs: {str(e)}\"}}\n\n"
                    await asyncio.sleep(5)
        
        except Exception as e:
            yield f"data: {{\"error\": \"Stream de logs interrompido: {str(e)}\"}}\n\n"
    
    return StreamingResponse(
        log_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Para nginx
        }
    )

# WEBSOCKET ENDPOINTS

# Initialize WebSocket manager if available
if websocket_available:
    try:
        websocket_manager = WebSocketManager()
        logger.info("WebSocket manager initialized")
    except Exception as e:
        logger.error(f"Failed to initialize WebSocket manager: {e}")
        websocket_available = False

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time communication"""
    if not websocket_available:
        await websocket.close(code=1013, reason="WebSocket not available")
        return

    # Accept connection and receive credentials
    await websocket.accept()

    try:
        credentials = await websocket.receive_text()
    except Exception:
        await websocket.close(code=1008, reason="Credentials required")
        return

    connection_id = str(uuid.uuid4())
    authenticator = websocket_manager.authenticator

    try:
        try:
            user = await authenticator.authenticate(credentials, connection_id)
        except Exception:
            user = await authenticator.authenticate_api_key(credentials, connection_id)
    except Exception as e:
        await websocket.close(code=1008, reason="Authentication failed")
        logger.warning(f"WebSocket authentication failed: {e}")
        return

    connection = await websocket_manager.connection_manager.connect(websocket, connection_id)
    await websocket_manager.connection_manager.authenticate_connection(connection_id, user)

    try:
        while True:
            data = await websocket.receive_text()
            await websocket_manager._handle_message(connection_id, data)
    except WebSocketDisconnect:
        logger.info(f"Client disconnected: {connection_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await websocket_manager.connection_manager.disconnect(connection_id)

@app.get("/api/websocket/status")
async def websocket_status():
    """Get WebSocket service status"""
    if not websocket_available:
        return {
            "available": False,
            "message": "WebSocket service not available",
            "active_connections": 0
        }
    
    try:
        stats = websocket_manager.get_stats()
        return {
            "available": True,
            "message": "WebSocket service running",
            "active_connections": stats.get("active_connections", 0),
            "endpoint": "/ws"
        }
    except Exception as e:
        return {
            "available": False,
            "message": f"WebSocket service error: {str(e)}",
            "active_connections": 0
        }

# HANDLER DE ERROS GLOBAIS

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Handler global para exceções não tratadas"""
    
    logger.error(f"💥 Exceção não tratada: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Erro interno do servidor",
            "error_id": f"err_{int(asyncio.get_event_loop().time())}"
        }
    )

# CONFIGURAÇÃO E STARTUP

def main():
    """Função principal para execução direta"""
    
    # Configura logging antes de tudo
    setup_logging()
    
    logger.info("🚀 Iniciando servidor...")
    
    # Configurações do servidor
    config = uvicorn.Config(
        app=app,
        host="0.0.0.0",
        port=8000,
        reload=settings.log_level == "DEBUG",
        access_log=False,  # Usamos nosso próprio middleware
        log_config=None   # Usamos loguru
    )
    
    server = uvicorn.Server(config)
    
    try:
        server.run()
    except KeyboardInterrupt:
        logger.info("👋 Servidor interrompido pelo usuário")
    except Exception as e:
        logger.error(f"💥 Erro fatal no servidor: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()