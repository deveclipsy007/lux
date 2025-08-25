"""
Sistema de Eventos WebSocket para Evolution API

Define:
- Tipos de eventos
- Estruturas de eventos
- Serialização/Deserialização
- Validação de eventos

Autor: AgnoMaster - Evolution API WebSocket Expert
Data: 2025-01-24
"""

import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Union, List
from dataclasses import dataclass, field
from enum import Enum
from pydantic import BaseModel, Field, validator


class EventType(str, Enum):
    """Tipos de eventos WebSocket"""
    
    # Eventos de Conexão
    CONNECTION_ESTABLISHED = "connection_established"
    CONNECTION_LOST = "connection_lost"
    PING = "ping"
    PONG = "pong"
    
    # Eventos de Autenticação
    AUTHENTICATE = "authenticate"
    AUTHENTICATION_SUCCESS = "authentication_success"
    AUTHENTICATION_FAILED = "authentication_failed"
    TOKEN_EXPIRED = "token_expired"
    
    # Eventos de Subscrição
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"
    SUBSCRIPTION_CONFIRMED = "subscription_confirmed"
    SUBSCRIPTION_FAILED = "subscription_failed"
    
    # Eventos de WhatsApp/Evolution API
    INSTANCE_STATUS_CHANGED = "instance_status_changed"
    INSTANCE_CREATED = "instance_created"
    INSTANCE_DELETED = "instance_deleted"
    INSTANCE_CONNECTED = "instance_connected"
    INSTANCE_DISCONNECTED = "instance_disconnected"
    QR_CODE_GENERATED = "qr_code_generated"
    
    # Eventos de Mensagens
    MESSAGE_RECEIVED = "message_received"
    MESSAGE_SENT = "message_sent"
    MESSAGE_DELIVERED = "message_delivered"
    MESSAGE_READ = "message_read"
    MESSAGE_FAILED = "message_failed"
    
    # Eventos de Agentes
    AGENT_CREATED = "agent_created"
    AGENT_UPDATED = "agent_updated"
    AGENT_DELETED = "agent_deleted"
    AGENT_MATERIALIZED = "agent_materialized"
    AGENT_RESPONSE = "agent_response"
    AGENT_ERROR = "agent_error"
    
    # Eventos do Sistema
    SYSTEM_STATUS = "system_status"
    SYSTEM_ERROR = "system_error"
    SYSTEM_MAINTENANCE = "system_maintenance"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    
    # Eventos de Usuário
    USER_ACTIVITY = "user_activity"
    USER_LOGGED_IN = "user_logged_in"
    USER_LOGGED_OUT = "user_logged_out"
    
    # Eventos de Monitoramento
    PERFORMANCE_METRICS = "performance_metrics"
    HEALTH_CHECK = "health_check"
    LOG_ENTRY = "log_entry"


class EventPriority(str, Enum):
    """Prioridade de eventos"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class EventCategory(str, Enum):
    """Categoria de eventos"""
    CONNECTION = "connection"
    AUTHENTICATION = "authentication"
    SUBSCRIPTION = "subscription"
    WHATSAPP = "whatsapp"
    AGENT = "agent"
    SYSTEM = "system"
    USER = "user"
    MONITORING = "monitoring"


# Mapeamento de tipos para categorias
EVENT_CATEGORIES = {
    # Connection
    EventType.CONNECTION_ESTABLISHED: EventCategory.CONNECTION,
    EventType.CONNECTION_LOST: EventCategory.CONNECTION,
    EventType.PING: EventCategory.CONNECTION,
    EventType.PONG: EventCategory.CONNECTION,
    
    # Authentication
    EventType.AUTHENTICATE: EventCategory.AUTHENTICATION,
    EventType.AUTHENTICATION_SUCCESS: EventCategory.AUTHENTICATION,
    EventType.AUTHENTICATION_FAILED: EventCategory.AUTHENTICATION,
    EventType.TOKEN_EXPIRED: EventCategory.AUTHENTICATION,
    
    # Subscription
    EventType.SUBSCRIBE: EventCategory.SUBSCRIPTION,
    EventType.UNSUBSCRIBE: EventCategory.SUBSCRIPTION,
    EventType.SUBSCRIPTION_CONFIRMED: EventCategory.SUBSCRIPTION,
    EventType.SUBSCRIPTION_FAILED: EventCategory.SUBSCRIPTION,
    
    # WhatsApp
    EventType.INSTANCE_STATUS_CHANGED: EventCategory.WHATSAPP,
    EventType.INSTANCE_CREATED: EventCategory.WHATSAPP,
    EventType.INSTANCE_DELETED: EventCategory.WHATSAPP,
    EventType.INSTANCE_CONNECTED: EventCategory.WHATSAPP,
    EventType.INSTANCE_DISCONNECTED: EventCategory.WHATSAPP,
    EventType.QR_CODE_GENERATED: EventCategory.WHATSAPP,
    EventType.MESSAGE_RECEIVED: EventCategory.WHATSAPP,
    EventType.MESSAGE_SENT: EventCategory.WHATSAPP,
    EventType.MESSAGE_DELIVERED: EventCategory.WHATSAPP,
    EventType.MESSAGE_READ: EventCategory.WHATSAPP,
    EventType.MESSAGE_FAILED: EventCategory.WHATSAPP,
    
    # Agent
    EventType.AGENT_CREATED: EventCategory.AGENT,
    EventType.AGENT_UPDATED: EventCategory.AGENT,
    EventType.AGENT_DELETED: EventCategory.AGENT,
    EventType.AGENT_MATERIALIZED: EventCategory.AGENT,
    EventType.AGENT_RESPONSE: EventCategory.AGENT,
    EventType.AGENT_ERROR: EventCategory.AGENT,
    
    # System
    EventType.SYSTEM_STATUS: EventCategory.SYSTEM,
    EventType.SYSTEM_ERROR: EventCategory.SYSTEM,
    EventType.SYSTEM_MAINTENANCE: EventCategory.SYSTEM,
    EventType.RATE_LIMIT_EXCEEDED: EventCategory.SYSTEM,
    
    # User
    EventType.USER_ACTIVITY: EventCategory.USER,
    EventType.USER_LOGGED_IN: EventCategory.USER,
    EventType.USER_LOGGED_OUT: EventCategory.USER,
    
    # Monitoring
    EventType.PERFORMANCE_METRICS: EventCategory.MONITORING,
    EventType.HEALTH_CHECK: EventCategory.MONITORING,
    EventType.LOG_ENTRY: EventCategory.MONITORING,
}


@dataclass
class WebSocketEvent:
    """Evento WebSocket"""
    type: EventType
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    connection_id: Optional[str] = None
    user_id: Optional[str] = None
    priority: EventPriority = EventPriority.NORMAL
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def category(self) -> EventCategory:
        return EVENT_CATEGORIES.get(self.type, EventCategory.SYSTEM)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário"""
        return {
            "type": self.type.value,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "connection_id": self.connection_id,
            "user_id": self.user_id,
            "priority": self.priority.value,
            "category": self.category.value,
            "metadata": self.metadata
        }
    
    def to_json(self) -> str:
        """Converte para JSON"""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WebSocketEvent':
        """Cria evento a partir de dicionário"""
        return cls(
            type=EventType(data['type']),
            data=data.get('data', {}),
            timestamp=datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00')),
            connection_id=data.get('connection_id'),
            user_id=data.get('user_id'),
            priority=EventPriority(data.get('priority', EventPriority.NORMAL.value)),
            metadata=data.get('metadata', {})
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> 'WebSocketEvent':
        """Cria evento a partir de JSON"""
        data = json.loads(json_str)
        return cls.from_dict(data)


# Schemas Pydantic para validação
class WebSocketEventSchema(BaseModel):
    """Schema para validação de eventos"""
    type: EventType
    data: Dict[str, Any] = Field(default_factory=dict)
    timestamp: Optional[datetime] = None
    connection_id: Optional[str] = None
    user_id: Optional[str] = None
    priority: EventPriority = EventPriority.NORMAL
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @validator('timestamp', pre=True, always=True)
    def set_timestamp(cls, v):
        return v or datetime.now(timezone.utc)
    
    def to_event(self) -> WebSocketEvent:
        """Converte para WebSocketEvent"""
        return WebSocketEvent(**self.dict())


# Eventos específicos com schemas
class AuthenticationEventData(BaseModel):
    """Dados de evento de autenticação"""
    token: Optional[str] = None
    user_id: Optional[str] = None
    username: Optional[str] = None
    error: Optional[str] = None
    expires_at: Optional[datetime] = None


class SubscriptionEventData(BaseModel):
    """Dados de evento de subscrição"""
    subscription_type: str
    success: bool = True
    error: Optional[str] = None


class InstanceEventData(BaseModel):
    """Dados de evento de instância"""
    instance_id: str
    instance_name: str
    status: str
    qr_code: Optional[str] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MessageEventData(BaseModel):
    """Dados de evento de mensagem"""
    message_id: str
    instance_id: str
    from_number: str
    to_number: Optional[str] = None
    message_type: str
    content: str
    timestamp: datetime
    status: Optional[str] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentEventData(BaseModel):
    """Dados de evento de agente"""
    agent_id: str
    agent_name: str
    action: str
    status: str
    response: Optional[str] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SystemEventData(BaseModel):
    """Dados de evento do sistema"""
    component: str
    status: str
    message: str
    error: Optional[str] = None
    metrics: Dict[str, Any] = Field(default_factory=dict)


class PerformanceEventData(BaseModel):
    """Dados de evento de performance"""
    cpu_usage: float
    memory_usage: float
    active_connections: int
    requests_per_second: float
    response_time_avg: float
    error_rate: float
    timestamp: datetime


# Factory functions para criar eventos específicos
def create_connection_event(connection_id: str, connected: bool = True) -> WebSocketEvent:
    """Cria evento de conexão"""
    event_type = EventType.CONNECTION_ESTABLISHED if connected else EventType.CONNECTION_LOST
    return WebSocketEvent(
        type=event_type,
        connection_id=connection_id,
        data={
            "connection_id": connection_id,
            "connected": connected,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )


def create_authentication_event(success: bool, user_id: Optional[str] = None, 
                               username: Optional[str] = None, error: Optional[str] = None) -> WebSocketEvent:
    """Cria evento de autenticação"""
    event_type = EventType.AUTHENTICATION_SUCCESS if success else EventType.AUTHENTICATION_FAILED
    data = AuthenticationEventData(
        user_id=user_id,
        username=username,
        error=error
    ).dict(exclude_none=True)
    
    return WebSocketEvent(
        type=event_type,
        user_id=user_id,
        data=data,
        priority=EventPriority.HIGH
    )


def create_instance_event(event_type: EventType, instance_id: str, instance_name: str, 
                         status: str, qr_code: Optional[str] = None, 
                         error: Optional[str] = None) -> WebSocketEvent:
    """Cria evento de instância"""
    data = InstanceEventData(
        instance_id=instance_id,
        instance_name=instance_name,
        status=status,
        qr_code=qr_code,
        error=error
    ).dict(exclude_none=True)
    
    priority = EventPriority.HIGH if error else EventPriority.NORMAL
    
    return WebSocketEvent(
        type=event_type,
        data=data,
        priority=priority
    )


def create_message_event(event_type: EventType, message_id: str, instance_id: str,
                        from_number: str, content: str, message_type: str = "text",
                        to_number: Optional[str] = None, status: Optional[str] = None,
                        error: Optional[str] = None) -> WebSocketEvent:
    """Cria evento de mensagem"""
    data = MessageEventData(
        message_id=message_id,
        instance_id=instance_id,
        from_number=from_number,
        to_number=to_number,
        message_type=message_type,
        content=content,
        timestamp=datetime.now(timezone.utc),
        status=status,
        error=error
    ).dict(exclude_none=True)
    
    priority = EventPriority.HIGH if error else EventPriority.NORMAL
    
    return WebSocketEvent(
        type=event_type,
        data=data,
        priority=priority
    )


def create_agent_event(event_type: EventType, agent_id: str, agent_name: str,
                      action: str, status: str, response: Optional[str] = None,
                      error: Optional[str] = None, execution_time: Optional[float] = None) -> WebSocketEvent:
    """Cria evento de agente"""
    data = AgentEventData(
        agent_id=agent_id,
        agent_name=agent_name,
        action=action,
        status=status,
        response=response,
        error=error,
        execution_time=execution_time
    ).dict(exclude_none=True)
    
    priority = EventPriority.HIGH if error else EventPriority.NORMAL
    
    return WebSocketEvent(
        type=event_type,
        data=data,
        priority=priority
    )


def create_system_event(event_type: EventType, component: str, status: str,
                       message: str, error: Optional[str] = None,
                       metrics: Optional[Dict[str, Any]] = None) -> WebSocketEvent:
    """Cria evento do sistema"""
    data = SystemEventData(
        component=component,
        status=status,
        message=message,
        error=error,
        metrics=metrics or {}
    ).dict(exclude_none=True)
    
    priority = EventPriority.CRITICAL if error else EventPriority.NORMAL
    
    return WebSocketEvent(
        type=event_type,
        data=data,
        priority=priority
    )


def create_performance_event(cpu_usage: float, memory_usage: float, 
                            active_connections: int, requests_per_second: float,
                            response_time_avg: float, error_rate: float) -> WebSocketEvent:
    """Cria evento de performance"""
    data = PerformanceEventData(
        cpu_usage=cpu_usage,
        memory_usage=memory_usage,
        active_connections=active_connections,
        requests_per_second=requests_per_second,
        response_time_avg=response_time_avg,
        error_rate=error_rate,
        timestamp=datetime.now(timezone.utc)
    ).dict()
    
    return WebSocketEvent(
        type=EventType.PERFORMANCE_METRICS,
        data=data,
        priority=EventPriority.LOW
    )


# Utilitários
def filter_events_by_category(events: List[WebSocketEvent], category: EventCategory) -> List[WebSocketEvent]:
    """Filtra eventos por categoria"""
    return [event for event in events if event.category == category]


def filter_events_by_priority(events: List[WebSocketEvent], min_priority: EventPriority) -> List[WebSocketEvent]:
    """Filtra eventos por prioridade mínima"""
    priority_order = {
        EventPriority.LOW: 0,
        EventPriority.NORMAL: 1,
        EventPriority.HIGH: 2,
        EventPriority.CRITICAL: 3
    }
    
    min_level = priority_order[min_priority]
    return [event for event in events if priority_order[event.priority] >= min_level]


def sort_events_by_timestamp(events: List[WebSocketEvent], reverse: bool = False) -> List[WebSocketEvent]:
    """Ordena eventos por timestamp"""
    return sorted(events, key=lambda e: e.timestamp, reverse=reverse)


def group_events_by_type(events: List[WebSocketEvent]) -> Dict[EventType, List[WebSocketEvent]]:
    """Agrupa eventos por tipo"""
    groups = {}
    for event in events:
        if event.type not in groups:
            groups[event.type] = []
        groups[event.type].append(event)
    return groups
