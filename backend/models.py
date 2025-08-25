"""
Modelos de dados e estruturas auxiliares

Define classes e estruturas de dados para armazenamento em memória,
cache e manipulação de dados internos da aplicação.

Diferente dos schemas (que são para validação/serialização da API),
estes modelos são usados internamente pela lógica de negócio.

Autor: Agno SDK Agent Generator  
Data: 2025-01-24
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from enum import Enum
from dataclasses import dataclass, field
from pathlib import Path
import json
import hashlib

# ENUMS E CONSTANTES

class AgentStatus(str, Enum):
    """Status possíveis de um agente"""
    DRAFT = "draft"                    # Rascunho, ainda não gerado
    GENERATED = "generated"            # Código gerado, mas não materializado  
    MATERIALIZED = "materialized"      # Código salvo no servidor
    RUNNING = "running"                # Agente em execução
    STOPPED = "stopped"                # Agente parado
    ERROR = "error"                    # Erro na execução

class ConnectionState(str, Enum):
    """Estados de conexão para integrações"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"
    TIMEOUT = "timeout"

class MessageType(str, Enum):
    """Tipos de mensagem suportados"""
    TEXT = "text"
    IMAGE = "image"
    DOCUMENT = "document" 
    AUDIO = "audio"
    VIDEO = "video"
    LOCATION = "location"
    CONTACT = "contact"

class EventType(str, Enum):
    """Tipos de eventos do sistema"""
    AGENT_CREATED = "agent_created"
    AGENT_UPDATED = "agent_updated"
    AGENT_DELETED = "agent_deleted"
    AGENT_STARTED = "agent_started"
    AGENT_STOPPED = "agent_stopped"
    MESSAGE_RECEIVED = "message_received"
    MESSAGE_SENT = "message_sent"
    CONNECTION_CHANGED = "connection_changed"
    ERROR_OCCURRED = "error_occurred"

# MODELOS PRINCIPAIS

@dataclass
class Agent:
    """Modelo principal de um agente"""
    
    id: str
    name: str
    specialization: str
    instructions: str
    tools: List[str]
    status: AgentStatus = AgentStatus.DRAFT
    
    # Metadados
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    created_by: str = "system"
    
    # Arquivos gerados
    generated_files: List['GeneratedFile'] = field(default_factory=list)
    materialized_path: Optional[Path] = None
    
    # Runtime
    process_id: Optional[int] = None
    last_activity: Optional[datetime] = None
    
    # Estatísticas
    messages_processed: int = 0
    uptime_seconds: int = 0
    error_count: int = 0
    
    # Configurações
    config: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Inicialização pós-criação"""
        if not self.id:
            self.id = self.generate_id()
    
    @staticmethod
    def generate_id() -> str:
        """Gera ID único para o agente"""
        timestamp = int(datetime.now().timestamp() * 1000)
        return f"agent_{timestamp}"
    
    def update_activity(self):
        """Atualiza timestamp da última atividade"""
        self.last_activity = datetime.now()
        self.updated_at = datetime.now()
    
    def add_file(self, path: str, content: str) -> 'GeneratedFile':
        """Adiciona arquivo gerado ao agente"""
        file_obj = GeneratedFile(
            path=path,
            content=content,
            agent_id=self.id
        )
        self.generated_files.append(file_obj)
        return file_obj
    
    def get_config_hash(self) -> str:
        """Gera hash da configuração atual"""
        config_str = json.dumps({
            'name': self.name,
            'specialization': self.specialization, 
            'instructions': self.instructions,
            'tools': sorted(self.tools)
        }, sort_keys=True)
        
        return hashlib.md5(config_str.encode()).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário"""
        return {
            'id': self.id,
            'name': self.name,
            'specialization': self.specialization,
            'instructions': self.instructions,
            'tools': self.tools,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'messages_processed': self.messages_processed,
            'uptime_seconds': self.uptime_seconds,
            'error_count': self.error_count,
            'config': self.config,
            'integrations': self.config.get('integrations')
        }


@dataclass
class GeneratedFile:
    """Arquivo gerado para um agente"""
    
    path: str
    content: str
    agent_id: str
    
    # Metadados
    created_at: datetime = field(default_factory=datetime.now)
    size_bytes: int = field(init=False)
    content_hash: str = field(init=False)
    
    def __post_init__(self):
        """Calcula metadados após criação"""
        self.size_bytes = len(self.content.encode('utf-8'))
        self.content_hash = hashlib.sha256(self.content.encode()).hexdigest()
    
    @property
    def filename(self) -> str:
        """Extrai nome do arquivo do path"""
        return Path(self.path).name
    
    @property
    def directory(self) -> str:
        """Extrai diretório do path"""
        return str(Path(self.path).parent)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário"""
        return {
            'path': self.path,
            'content': self.content,
            'size_bytes': self.size_bytes,
            'content_hash': self.content_hash,
            'created_at': self.created_at.isoformat()
        }

@dataclass 
class WhatsAppInstance:
    """Modelo de uma instância WhatsApp"""
    
    instance_id: str
    agent_id: Optional[str] = None
    
    # Estado da conexão
    status: ConnectionState = ConnectionState.DISCONNECTED
    qr_code: Optional[str] = None
    qr_expires_at: Optional[datetime] = None
    
    # Dados da conta conectada
    phone_number: Optional[str] = None
    profile_name: Optional[str] = None
    profile_picture: Optional[str] = None
    
    # Configurações
    webhook_url: Optional[str] = None
    auto_reconnect: bool = True
    
    # Metadados
    created_at: datetime = field(default_factory=datetime.now)
    connected_at: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    
    # Estatísticas
    messages_sent: int = 0
    messages_received: int = 0
    connection_attempts: int = 0
    
    def is_qr_expired(self) -> bool:
        """Verifica se QR Code expirou"""
        if not self.qr_expires_at:
            return True
        return datetime.now() > self.qr_expires_at
    
    def update_qr(self, qr_code: str, expires_in_seconds: int = 60):
        """Atualiza QR Code com nova expiração"""
        self.qr_code = qr_code
        self.qr_expires_at = datetime.now() + timedelta(seconds=expires_in_seconds)
    
    def mark_connected(self, phone_number: str, profile_name: str = None):
        """Marca instância como conectada"""
        self.status = ConnectionState.CONNECTED
        self.phone_number = phone_number
        self.profile_name = profile_name
        self.connected_at = datetime.now()
        self.last_seen = datetime.now()
        self.qr_code = None
        self.qr_expires_at = None
    
    def mark_disconnected(self):
        """Marca instância como desconectada"""
        self.status = ConnectionState.DISCONNECTED
        self.last_seen = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário"""
        return {
            'instance_id': self.instance_id,
            'agent_id': self.agent_id,
            'status': self.status,
            'phone_number': self.phone_number,
            'profile_name': self.profile_name,
            'webhook_url': self.webhook_url,
            'created_at': self.created_at.isoformat(),
            'connected_at': self.connected_at.isoformat() if self.connected_at else None,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
            'messages_sent': self.messages_sent,
            'messages_received': self.messages_received,
            'qr_expired': self.is_qr_expired()
        }

@dataclass
class Message:
    """Modelo de uma mensagem"""
    
    id: str
    instance_id: str
    agent_id: Optional[str] = None
    
    # Participantes
    from_number: str = ""
    to_number: str = ""
    from_me: bool = False
    
    # Conteúdo
    message_type: MessageType = MessageType.TEXT
    content: str = ""
    media_url: Optional[str] = None
    
    # Metadados
    timestamp: datetime = field(default_factory=datetime.now)
    delivered: bool = False
    read: bool = False
    
    # Contexto da conversa
    chat_id: str = ""
    reply_to: Optional[str] = None
    
    def __post_init__(self):
        """Inicialização pós-criação"""
        if not self.id:
            self.id = self.generate_id()
        
        if not self.chat_id:
            self.chat_id = self.from_number if not self.from_me else self.to_number
    
    @staticmethod
    def generate_id() -> str:
        """Gera ID único para mensagem"""
        timestamp = int(datetime.now().timestamp() * 1000)
        return f"msg_{timestamp}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário"""
        return {
            'id': self.id,
            'instance_id': self.instance_id,
            'agent_id': self.agent_id,
            'from_number': self.from_number,
            'to_number': self.to_number,
            'from_me': self.from_me,
            'message_type': self.message_type,
            'content': self.content,
            'timestamp': self.timestamp.isoformat(),
            'delivered': self.delivered,
            'read': self.read,
            'chat_id': self.chat_id
        }

@dataclass
class Conversation:
    """Modelo de uma conversa/chat"""
    
    chat_id: str
    instance_id: str
    agent_id: Optional[str] = None
    
    # Participantes
    contact_number: str = ""
    contact_name: Optional[str] = None
    
    # Estado da conversa
    active: bool = True
    last_message_at: Optional[datetime] = None
    
    # Mensagens
    messages: List[Message] = field(default_factory=list)
    
    # Metadados
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    # Contexto do agente
    context: Dict[str, Any] = field(default_factory=dict)
    
    def add_message(self, message: Message):
        """Adiciona mensagem à conversa"""
        self.messages.append(message)
        self.last_message_at = message.timestamp
        self.updated_at = datetime.now()
    
    def get_recent_messages(self, limit: int = 10) -> List[Message]:
        """Obtém mensagens recentes"""
        return sorted(self.messages, key=lambda m: m.timestamp, reverse=True)[:limit]
    
    def get_context_summary(self) -> str:
        """Gera resumo do contexto da conversa"""
        recent = self.get_recent_messages(5)
        if not recent:
            return "Conversa nova"
        
        summary_parts = []
        for msg in reversed(recent):  # Ordem cronológica
            sender = "Cliente" if not msg.from_me else "Agente"
            summary_parts.append(f"{sender}: {msg.content[:50]}...")
        
        return " | ".join(summary_parts)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário"""
        return {
            'chat_id': self.chat_id,
            'instance_id': self.instance_id,
            'agent_id': self.agent_id,
            'contact_number': self.contact_number,
            'contact_name': self.contact_name,
            'active': self.active,
            'message_count': len(self.messages),
            'last_message_at': self.last_message_at.isoformat() if self.last_message_at else None,
            'created_at': self.created_at.isoformat(),
            'context_summary': self.get_context_summary()
        }

@dataclass
class SystemEvent:
    """Modelo de eventos do sistema"""
    
    id: str
    event_type: EventType
    
    # Dados do evento
    source: str = "system"
    target_id: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    
    # Metadados
    timestamp: datetime = field(default_factory=datetime.now)
    processed: bool = False
    retry_count: int = 0
    
    def __post_init__(self):
        """Inicialização pós-criação"""
        if not self.id:
            self.id = self.generate_id()
    
    @staticmethod
    def generate_id() -> str:
        """Gera ID único para evento"""
        timestamp = int(datetime.now().timestamp() * 1000)
        return f"event_{timestamp}"
    
    def mark_processed(self):
        """Marca evento como processado"""
        self.processed = True
    
    def increment_retry(self):
        """Incrementa contador de tentativas"""
        self.retry_count += 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário"""
        return {
            'id': self.id,
            'event_type': self.event_type,
            'source': self.source,
            'target_id': self.target_id,
            'data': self.data,
            'timestamp': self.timestamp.isoformat(),
            'processed': self.processed,
            'retry_count': self.retry_count
        }

# CLASSES DE CACHE E ARMAZENAMENTO

class InMemoryStore:
    """Store em memória para dados da aplicação"""
    
    def __init__(self):
        self._agents: Dict[str, Agent] = {}
        self._instances: Dict[str, WhatsAppInstance] = {}
        self._messages: Dict[str, Message] = {}
        self._conversations: Dict[str, Conversation] = {}
        self._events: List[SystemEvent] = []
        
        # Índices para busca rápida
        self._agent_by_name: Dict[str, str] = {}
        self._conversations_by_contact: Dict[str, Set[str]] = {}
        self._messages_by_chat: Dict[str, List[str]] = {}
        
        # Lock para operações thread-safe
        self._lock = asyncio.Lock()
    
    # Operações com Agentes
    async def add_agent(self, agent: Agent) -> bool:
        """Adiciona agente ao store"""
        async with self._lock:
            if agent.id in self._agents:
                return False
            
            if agent.name in self._agent_by_name:
                return False  # Nome já existe
            
            self._agents[agent.id] = agent
            self._agent_by_name[agent.name] = agent.id
            return True
    
    async def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Obtém agente por ID"""
        return self._agents.get(agent_id)
    
    async def get_agent_by_name(self, name: str) -> Optional[Agent]:
        """Obtém agente por nome"""
        agent_id = self._agent_by_name.get(name)
        if agent_id:
            return self._agents.get(agent_id)
        return None
    
    async def list_agents(self) -> List[Agent]:
        """Lista todos os agentes"""
        return list(self._agents.values())
    
    async def update_agent(self, agent: Agent) -> bool:
        """Atualiza agente existente"""
        async with self._lock:
            if agent.id not in self._agents:
                return False
            
            old_agent = self._agents[agent.id]
            
            # Atualiza índice se nome mudou
            if old_agent.name != agent.name:
                if agent.name in self._agent_by_name:
                    return False  # Nome já existe
                
                del self._agent_by_name[old_agent.name]
                self._agent_by_name[agent.name] = agent.id
            
            self._agents[agent.id] = agent
            return True
    
    async def delete_agent(self, agent_id: str) -> bool:
        """Remove agente do store"""
        async with self._lock:
            agent = self._agents.get(agent_id)
            if not agent:
                return False
            
            del self._agents[agent_id]
            del self._agent_by_name[agent.name]
            return True
    
    # Operações com Instâncias WhatsApp
    async def add_instance(self, instance: WhatsAppInstance) -> bool:
        """Adiciona instância ao store"""
        async with self._lock:
            if instance.instance_id in self._instances:
                return False
            
            self._instances[instance.instance_id] = instance
            return True
    
    async def get_instance(self, instance_id: str) -> Optional[WhatsAppInstance]:
        """Obtém instância por ID"""
        return self._instances.get(instance_id)
    
    async def update_instance(self, instance: WhatsAppInstance) -> bool:
        """Atualiza instância existente"""
        async with self._lock:
            if instance.instance_id not in self._instances:
                return False
            
            self._instances[instance.instance_id] = instance
            return True
    
    # Operações com Mensagens
    async def add_message(self, message: Message) -> bool:
        """Adiciona mensagem ao store"""
        async with self._lock:
            if message.id in self._messages:
                return False
            
            self._messages[message.id] = message
            
            # Atualiza índice por chat
            if message.chat_id not in self._messages_by_chat:
                self._messages_by_chat[message.chat_id] = []
            self._messages_by_chat[message.chat_id].append(message.id)
            
            return True
    
    async def get_messages_by_chat(self, chat_id: str, limit: int = 50) -> List[Message]:
        """Obtém mensagens por chat"""
        message_ids = self._messages_by_chat.get(chat_id, [])
        messages = [self._messages[mid] for mid in message_ids[-limit:]]
        return sorted(messages, key=lambda m: m.timestamp)
    
    # Operações com Conversas
    async def add_conversation(self, conversation: Conversation) -> bool:
        """Adiciona conversa ao store"""
        async with self._lock:
            if conversation.chat_id in self._conversations:
                return False
            
            self._conversations[conversation.chat_id] = conversation
            
            # Atualiza índice por contato
            if conversation.contact_number not in self._conversations_by_contact:
                self._conversations_by_contact[conversation.contact_number] = set()
            self._conversations_by_contact[conversation.contact_number].add(conversation.chat_id)
            
            return True
    
    async def get_conversation(self, chat_id: str) -> Optional[Conversation]:
        """Obtém conversa por ID"""
        return self._conversations.get(chat_id)
    
    # Operações com Eventos
    async def add_event(self, event: SystemEvent) -> bool:
        """Adiciona evento ao store"""
        async with self._lock:
            self._events.append(event)
            
            # Mantém apenas últimos 1000 eventos
            if len(self._events) > 1000:
                self._events = self._events[-1000:]
            
            return True
    
    async def get_pending_events(self, limit: int = 10) -> List[SystemEvent]:
        """Obtém eventos pendentes de processamento"""
        pending = [e for e in self._events if not e.processed]
        return sorted(pending, key=lambda e: e.timestamp)[:limit]
    
    # Estatísticas
    async def get_stats(self) -> Dict[str, Any]:
        """Obtém estatísticas do store"""
        return {
            'agents_count': len(self._agents),
            'instances_count': len(self._instances),
            'messages_count': len(self._messages),
            'conversations_count': len(self._conversations),
            'events_count': len(self._events),
            'pending_events': len([e for e in self._events if not e.processed])
        }

# Instância global do store
app_store = InMemoryStore()