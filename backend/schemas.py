"""
Schemas Pydantic para validação e serialização de dados

Define todos os modelos de dados usados pela API, incluindo:
- Estruturas de entrada para criação de agentes
- Modelos de resposta para endpoints
- Validação de dados de integração com Evolution API
- Schemas para logs e sistema de monitoramento

Autor: Agno SDK Agent Generator  
Data: 2025-01-24
"""

from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from enum import Enum

from pydantic import BaseModel, Field, validator, root_validator, HttpUrl, EmailStr
import re

# ENUMS E CONSTANTES

class AgentSpecialization(str, Enum):
    """Especializações disponíveis para agentes"""
    ATENDIMENTO = "Atendimento"
    AGENDAMENTO = "Agendamento" 
    VENDAS = "Vendas"
    SUPORTE = "Suporte"
    CUSTOM = "Custom"

class AgentTool(str, Enum):
    """Tools/integrações disponíveis para agentes"""
    WHATSAPP = "whatsapp"
    EMAIL = "email"
    CALENDAR = "calendar"
    WEBHOOKS = "webhooks" 
    DATABASE = "database"

class WhatsAppInstanceStatus(str, Enum):
    """Status possíveis de uma instância WhatsApp"""
    UNKNOWN = "UNKNOWN"
    DISCONNECTED = "DISCONNECTED"
    CONNECTING = "CONNECTING"
    QR_READY = "QR_READY" 
    CONNECTED = "CONNECTED"
    ERROR = "ERROR"

class LogLevel(str, Enum):
    """Níveis de log disponíveis"""
    DEBUG = "DEBUG"
    INFO = "INFO" 
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


# -----------------------------------------------------
#   CONFIGURAÇÕES DE INTEGRAÇÃO
# -----------------------------------------------------


class WhatsAppIntegrationConfig(BaseModel):
    """Configuração para integração com WhatsApp"""

    api_url: HttpUrl = Field(..., description="URL base da API do WhatsApp")
    api_key: str = Field(
        ..., min_length=10, description="Token de acesso para Evolution API"
    )
    phone_number: str = Field(
        ...,
        pattern=r"^\+?\d{10,15}$",
        description="Número de telefone em formato internacional",
    )


class EmailIntegrationConfig(BaseModel):
    """Configuração para integração com serviço de e-mail"""

    smtp_server: HttpUrl = Field(..., description="URL do servidor SMTP")
    smtp_port: int = Field(
        ..., ge=1, le=65535, description="Porta do servidor SMTP"
    )
    from_email: EmailStr = Field(..., description="Endereço de e-mail remetente")


class IntegrationConfig(BaseModel):
    """Agrupa configurações de integrações disponíveis"""

    whatsapp: Optional[WhatsAppIntegrationConfig] = None
    email: Optional[EmailIntegrationConfig] = None


# SCHEMAS DE ENTRADA (REQUEST)

class AgentCreate(BaseModel):
    """Schema para criação de um novo agente"""
    
    agent_name: str = Field(
        ..., 
        min_length=3,
        max_length=40,
        description="Nome único do agente"
    )
    
    instructions: str = Field(
        ...,
        min_length=80,
        max_length=5000, 
        description="Instruções detalhadas para o comportamento do agente (system prompt)"
    )
    
    specialization: AgentSpecialization = Field(
        ...,
        description="Especialização do agente que define seu comportamento padrão"
    )
    
    tools: List[AgentTool] = Field(
        ...,
        min_items=1,
        description="Lista de ferramentas/integrações que o agente utilizará"
    )
    integrations: Optional[IntegrationConfig] = Field(
        None, description="Configurações das integrações selecionadas"
    )

    # Validação customizada do nome do agente
    @validator('agent_name')
    def validate_agent_name(cls, v):
        """Valida formato do nome do agente"""
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Nome deve conter apenas letras, números, hífen e underscore')
        
        # Lista de nomes reservados
        reserved_names = ['admin', 'api', 'system', 'test', 'default']
        if v.lower() in reserved_names:
            raise ValueError(f'Nome "{v}" é reservado pelo sistema')
            
        return v
    
    @validator('tools')
    def validate_tools(cls, v):
        """Valida lista de tools"""
        if not v:
            raise ValueError('Pelo menos uma ferramenta deve ser selecionada')
        
        # Remove duplicatas preservando ordem
        seen = set()
        unique_tools = []
        for tool in v:
            if tool not in seen:
                seen.add(tool)
                unique_tools.append(tool)

        return unique_tools

    @root_validator(skip_on_failure=True)
    def validate_integrations(cls, values):
        tools = values.get('tools', [])
        integrations: Optional[IntegrationConfig] = values.get('integrations')
        if AgentTool.WHATSAPP in tools and not (integrations and integrations.whatsapp):
            raise ValueError('Configuração de WhatsApp é obrigatória')
        if AgentTool.EMAIL in tools and not (integrations and integrations.email):
            raise ValueError('Configuração de E-mail é obrigatória')
        return values

    class Config:
        use_enum_values = True
        schema_extra = {
            "example": {
                "agent_name": "atendimento-bot",
                "instructions": "Você é um assistente especializado em atendimento ao cliente. Seja sempre educado, prestativo e busque resolver os problemas dos usuários de forma eficiente. Mantenha um tom amigável e profissional.",
                "specialization": "Atendimento",
                "tools": ["whatsapp", "email"]
            }
        }


class AgentUpdate(BaseModel):
    """Schema para atualização de um agente existente"""

    agent_name: Optional[str] = Field(
        None,
        min_length=3,
        max_length=40,
        description="Nome único do agente",
    )
    instructions: Optional[str] = Field(
        None,
        min_length=80,
        max_length=5000,
        description="Instruções detalhadas para o comportamento do agente",
    )
    specialization: Optional[AgentSpecialization] = Field(
        None, description="Especialização do agente"
    )
    tools: Optional[List[AgentTool]] = Field(
        None, description="Lista de ferramentas/integrações"
    )

    integrations: Optional[IntegrationConfig] = Field(
        None, description="Configurações das integrações selecionadas"
    )

    @validator("agent_name")
    def validate_agent_name(cls, v):
        if v is None:
            return v
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError(
                "Nome deve conter apenas letras, números, hífen e underscore"
            )
        reserved_names = ["admin", "api", "system", "test", "default"]
        if v.lower() in reserved_names:
            raise ValueError(f'Nome "{v}" é reservado pelo sistema')
        return v

    @validator("tools")
    def validate_tools(cls, v):
        if v is None:
            return v
        if not v:
            raise ValueError("Pelo menos uma ferramenta deve ser selecionada")
        seen = set()
        unique_tools = []
        for tool in v:
            if tool not in seen:
                seen.add(tool)
                unique_tools.append(tool)
        return unique_tools

    @root_validator(skip_on_failure=True)
    def validate_integrations(cls, values):
        tools = values.get('tools')
        integrations = values.get('integrations')
        if tools:
            if AgentTool.WHATSAPP in tools and not (integrations and integrations.whatsapp):
                raise ValueError('Configuração de WhatsApp é obrigatória')
            if AgentTool.EMAIL in tools and not (integrations and integrations.email):
                raise ValueError('Configuração de E-mail é obrigatória')
        return values

    class Config:
        use_enum_values = True


class AgentInfo(BaseModel):
    """Schema de resposta para um agente"""

    id: str = Field(..., description="ID do agente")
    name: str = Field(..., description="Nome do agente")
    specialization: AgentSpecialization = Field(
        ..., description="Especialização do agente"
    )
    instructions: str = Field(..., description="Instruções do agente")
    tools: List[AgentTool] = Field(
        ..., description="Lista de ferramentas/integrações"
    )
    integrations: Optional[IntegrationConfig] = Field(
        None, description="Configurações das integrações"
    )

    class Config:
        use_enum_values = True

class SendMessage(BaseModel):
    """Schema para envio de mensagens via WhatsApp"""
    
    instance_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="ID da instância WhatsApp"
    )
    
    to: str = Field(
        ...,
        description="Número do destinatário no formato internacional (ex: 5511999999999)"
    )
    
    message: str = Field(
        ...,
        min_length=1, 
        max_length=4096,
        description="Texto da mensagem a ser enviada"
    )
    
    @validator('to')
    def validate_phone_number(cls, v):
        """Valida formato do número de telefone"""
        # Remove caracteres não numéricos
        phone = re.sub(r'[^\d]', '', v)
        
        # Valida formato internacional básico
        if not re.match(r'^\d{10,15}$', phone):
            raise ValueError('Número deve estar no formato internacional (10-15 dígitos)')
        
        return phone
    
    class Config:
        schema_extra = {
            "example": {
                "instance_id": "agno-agent",
                "to": "5511999999999",
                "message": "Olá! Esta é uma mensagem de teste do seu agente."
            }
        }

class MaterializeRequest(BaseModel):
    """Schema para materialização de agente no servidor"""
    
    agent_name: str = Field(..., description="Nome do agente")
    files: List[Dict[str, str]] = Field(
        ...,
        description="Lista de arquivos com 'path' e 'content'"
    )
    
    @validator('files') 
    def validate_files(cls, v):
        """Valida estrutura dos arquivos"""
        if not v:
            raise ValueError('Lista de arquivos não pode estar vazia')
        
        required_keys = {'path', 'content'}
        for i, file_data in enumerate(v):
            if not isinstance(file_data, dict):
                raise ValueError(f'Arquivo {i} deve ser um objeto')
            
            missing_keys = required_keys - set(file_data.keys())
            if missing_keys:
                raise ValueError(f'Arquivo {i} está faltando chaves: {missing_keys}')
        
        return v

# SCHEMAS DE RESPOSTA (RESPONSE)

class FileData(BaseModel):
    """Dados de um arquivo gerado"""
    
    path: str = Field(..., description="Caminho relativo do arquivo")
    content: str = Field(..., description="Conteúdo do arquivo")
    
    class Config:
        schema_extra = {
            "example": {
                "path": "backend/main.py",
                "content": "#!/usr/bin/env python3\n# Código do agente...\n"
            }
        }

class AgentGeneratedFiles(BaseModel):
    """Resposta com arquivos gerados para um agente"""
    
    files: List[FileData] = Field(
        ...,
        description="Lista de arquivos gerados com path e conteúdo"
    )
    
    agent_name: str = Field(..., description="Nome do agente")
    specialization: str = Field(..., description="Especialização do agente") 
    tools: List[str] = Field(..., description="Ferramentas utilizadas")
    generated_at: datetime = Field(default_factory=datetime.now, description="Timestamp da geração")
    
    class Config:
        schema_extra = {
            "example": {
                "files": [
                    {
                        "path": "backend/main.py",
                        "content": "#!/usr/bin/env python3\n# Código principal..."
                    },
                    {
                        "path": "backend/agent.py", 
                        "content": "# Definição do agente..."
                    }
                ],
                "agent_name": "atendimento-bot",
                "specialization": "Atendimento",
                "tools": ["whatsapp", "email"],
                "generated_at": "2025-01-24T10:30:00Z"
            }
        }

class InstanceState(BaseModel):
    """Representa o resultado e o estado atual de uma instância"""

    status: str = Field("success", description="Resultado da consulta")
    state: str = Field(..., description="Estado atual da conexão")

class WppInstance(BaseModel):
    """Dados de uma instância WhatsApp"""
    
    instance_id: str = Field(..., description="ID único da instância")
    state: WhatsAppInstanceStatus = Field(
        WhatsAppInstanceStatus.UNKNOWN,
        description="Estado atual da conexão"
    )
    qr_code: Optional[str] = Field(
        None,
        alias="qr",
        description="QR Code em base64 (se disponível)"
    )
    phone_number: Optional[str] = Field(None, description="Número conectado")
    profile_name: Optional[str] = Field(None, description="Nome do perfil WhatsApp")
    webhook_url: Optional[str] = Field(None, description="URL do webhook configurado")
    created_at: datetime = Field(default_factory=datetime.now, description="Data de criação")
    last_seen: Optional[datetime] = Field(None, description="Última atividade")
    
    class Config:
        use_enum_values = True
        schema_extra = {
            "example": {
                "instance_id": "agno-agent",
                "state": "CONNECTED",
                "phone_number": "5511999999999", 
                "profile_name": "Meu Agente",
                "created_at": "2025-01-24T10:00:00Z"
            }
        }

class HealthResponse(BaseModel):
    """Resposta do health check"""
    
    status: str = Field(..., description="Status da aplicação")
    message: str = Field(..., description="Mensagem descritiva")
    version: str = Field(..., description="Versão da API")
    timestamp: float = Field(..., description="Timestamp Unix")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "healthy",
                "message": "All systems operational", 
                "version": "1.0.0",
                "timestamp": 1706097600.0
            }
        }

class LogEntry(BaseModel):
    """Entrada individual de log"""
    
    timestamp: str = Field(..., description="Timestamp formatado")
    level: LogLevel = Field(..., description="Nível do log")
    location: str = Field(..., description="Localização no código (arquivo:função:linha)")
    message: str = Field(..., description="Mensagem do log")
    raw: Optional[str] = Field(None, description="Linha raw do log se não parseável")
    
    class Config:
        use_enum_values = True
        schema_extra = {
            "example": {
                "timestamp": "2025-01-24 10:30:45",
                "level": "INFO",
                "location": "main:generate_agent:125",
                "message": "Gerando agente: atendimento-bot"
            }
        }

class LogsResponse(BaseModel):
    """Resposta da consulta de logs"""
    
    logs: List[LogEntry] = Field(..., description="Lista de entradas de log")
    total: int = Field(..., description="Total de logs retornados")
    level_filter: Optional[str] = Field(None, description="Filtro de nível aplicado")
    limit: int = Field(..., description="Limite de logs retornados")
    
    class Config:
        schema_extra = {
            "example": {
                "logs": [
                    {
                        "timestamp": "2025-01-24 10:30:45",
                        "level": "INFO", 
                        "location": "main:health_check:89",
                        "message": "Health check executado com sucesso"
                    }
                ],
                "total": 1,
                "level_filter": "INFO",
                "limit": 100
            }
        }

# SCHEMAS PARA EVOLUTION API

class EvolutionInstanceCreate(BaseModel):
    """Schema para criação de instância na Evolution API"""
    
    instanceName: str = Field(..., description="Nome da instância")
    integration: str = Field(default="WHATSAPP-BAILEYS", description="Tipo de integração")
    webhook_url: Optional[str] = Field(None, description="URL do webhook para eventos")
    
    class Config:
        schema_extra = {
            "example": {
                "instanceName": "agno-agent",
                "integration": "WHATSAPP-BAILEYS",
                "webhook_url": "https://myapi.com/webhook"
            }
        }

class EvolutionMessage(BaseModel):
    """Schema para envio de mensagens via Evolution"""
    
    number: str = Field(..., description="Número do destinatário")
    text: str = Field(..., description="Texto da mensagem")
    
    class Config:
        schema_extra = {
            "example": {
                "number": "5511999999999",
                "text": "Olá! Como posso ajudá-lo?"
            }
        }

class EvolutionWebhookConfig(BaseModel):
    """Schema para configuração de webhook"""
    
    url: str = Field(..., description="URL do endpoint webhook")
    events: List[str] = Field(
        default=["messages.upsert"],
        description="Lista de eventos a serem enviados"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "url": "https://myapi.com/webhook/whatsapp",
                "events": ["messages.upsert", "connection.update"]
            }
        }

# SCHEMAS DE WEBHOOK RECEBIDO

class WhatsAppContact(BaseModel):
    """Dados de contato do WhatsApp"""
    
    id: str = Field(..., description="ID do contato")
    name: Optional[str] = Field(None, description="Nome do contato")
    
class WhatsAppMessageKey(BaseModel):
    """Chave da mensagem WhatsApp"""
    
    remoteJid: str = Field(..., description="ID do chat/contato")
    fromMe: bool = Field(..., description="Indica se mensagem foi enviada por nós")
    id: str = Field(..., description="ID único da mensagem")
    
class WhatsAppMessage(BaseModel):
    """Mensagem recebida via webhook"""
    
    key: WhatsAppMessageKey = Field(..., description="Chave da mensagem")
    messageTimestamp: int = Field(..., description="Timestamp da mensagem")
    pushName: Optional[str] = Field(None, description="Nome do remetente")
    message: Optional[Dict[str, Any]] = Field(None, description="Conteúdo da mensagem")
    
class WhatsAppWebhookPayload(BaseModel):
    """Payload completo do webhook WhatsApp"""
    
    instance: str = Field(..., description="Nome da instância")
    data: Dict[str, Any] = Field(..., description="Dados do evento")
    type: str = Field(..., description="Tipo do evento")
    server_url: Optional[str] = Field(None, description="URL do servidor Evolution")
    
    class Config:
        schema_extra = {
            "example": {
                "instance": "agno-agent",
                "data": {
                    "messages": [
                        {
                            "key": {
                                "remoteJid": "5511999999999@s.whatsapp.net",
                                "fromMe": False,
                                "id": "msg_unique_id"
                            },
                            "messageTimestamp": 1706097600,
                            "pushName": "João Silva",
                            "message": {
                                "conversation": "Olá, preciso de ajuda!"
                            }
                        }
                    ]
                },
                "type": "messages.upsert",
                "server_url": "https://evolution-api.com"
            }
        }

# SCHEMAS DE CONFIGURAÇÃO

class AgentConfig(BaseModel):
    """Configuração de um agente gerado"""
    
    name: str = Field(..., description="Nome do agente")
    specialization: AgentSpecialization = Field(..., description="Especialização")
    instructions: str = Field(..., description="Instruções do system prompt")
    tools: List[AgentTool] = Field(..., description="Ferramentas habilitadas")
    
    # Configurações específicas por ferramenta
    whatsapp_config: Optional[Dict[str, Any]] = Field(None, description="Configurações WhatsApp")
    email_config: Optional[Dict[str, Any]] = Field(None, description="Configurações Email")
    calendar_config: Optional[Dict[str, Any]] = Field(None, description="Configurações Calendar")
    webhook_config: Optional[Dict[str, Any]] = Field(None, description="Configurações Webhooks")
    database_config: Optional[Dict[str, Any]] = Field(None, description="Configurações Banco")
    
    class Config:
        use_enum_values = True

# SCHEMAS DE ERRO

class APIError(BaseModel):
    """Estrutura padrão para erros da API"""
    
    detail: str = Field(..., description="Descrição do erro")
    error_code: Optional[str] = Field(None, description="Código do erro") 
    error_id: Optional[str] = Field(None, description="ID único do erro")
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp do erro")
    
    class Config:
        schema_extra = {
            "example": {
                "detail": "Nome do agente já existe",
                "error_code": "AGENT_NAME_EXISTS", 
                "error_id": "err_1706097600",
                "timestamp": "2025-01-24T10:30:00Z"
            }
        }

class ValidationError(BaseModel):
    """Erro de validação de campos"""
    
    field: str = Field(..., description="Nome do campo com erro")
    message: str = Field(..., description="Mensagem de erro")
    value: Optional[Any] = Field(None, description="Valor que causou o erro")
    
    class Config:
        schema_extra = {
            "example": {
                "field": "agent_name",
                "message": "Nome deve conter apenas letras, números, hífen e underscore",
                "value": "agente@inválido"
            }
        }

# SCHEMAS UTILITÁRIOS

class PaginatedResponse(BaseModel):
    """Response paginado genérico"""
    
    items: List[Any] = Field(..., description="Itens da página atual")
    total: int = Field(..., description="Total de itens")
    page: int = Field(..., description="Página atual")
    per_page: int = Field(..., description="Itens por página") 
    pages: int = Field(..., description="Total de páginas")
    
    class Config:
        schema_extra = {
            "example": {
                "items": [],
                "total": 150,
                "page": 1, 
                "per_page": 20,
                "pages": 8
            }
        }

class BulkOperationResponse(BaseModel):
    """Resposta para operações em lote"""
    
    success_count: int = Field(..., description="Número de operações bem-sucedidas")
    error_count: int = Field(..., description="Número de operações com erro")
    total: int = Field(..., description="Total de operações")
    errors: List[Dict[str, Any]] = Field(default=[], description="Lista de erros ocorridos")
    
    class Config:
        schema_extra = {
            "example": {
                "success_count": 18,
                "error_count": 2,
                "total": 20,
                "errors": [
                    {
                        "item": "agent-invalid",
                        "error": "Nome inválido"
                    }
                ]
            }
        }
