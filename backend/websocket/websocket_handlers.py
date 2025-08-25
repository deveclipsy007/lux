"""
Handlers de Eventos WebSocket para Evolution API

Implementa:
- Handlers específicos por tipo de evento
- Processamento assíncrono
- Integração com Evolution API
- Broadcasting inteligente
- Monitoramento de eventos

Autor: AgnoMaster - Evolution API WebSocket Expert
Data: 2025-01-24
"""

import asyncio
import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass
from abc import ABC, abstractmethod

from loguru import logger
import redis.asyncio as redis

from .websocket_events import (
    WebSocketEvent, EventType, EventPriority, EventCategory,
    create_instance_event, create_message_event, create_agent_event,
    create_system_event, create_performance_event
)
from .websocket_manager import WebSocketManager, SubscriptionType
from ..evolution import EvolutionService
from ..agno_service import AgnoService
from ..models import WhatsAppInstance, Message


class EventHandler(ABC):
    """Handler base para eventos"""
    
    def __init__(self, websocket_manager: WebSocketManager):
        self.websocket_manager = websocket_manager
        self.logger = logger
    
    @abstractmethod
    async def handle(self, event: WebSocketEvent) -> bool:
        """Processa o evento"""
        pass
    
    @property
    @abstractmethod
    def supported_events(self) -> List[EventType]:
        """Tipos de eventos suportados"""
        pass


class InstanceEventHandler(EventHandler):
    """Handler para eventos de instância WhatsApp"""
    
    def __init__(self, websocket_manager: WebSocketManager, evolution_service: EvolutionService):
        super().__init__(websocket_manager)
        self.evolution_service = evolution_service
    
    @property
    def supported_events(self) -> List[EventType]:
        return [
            EventType.INSTANCE_STATUS_CHANGED,
            EventType.INSTANCE_CREATED,
            EventType.INSTANCE_DELETED,
            EventType.INSTANCE_CONNECTED,
            EventType.INSTANCE_DISCONNECTED,
            EventType.QR_CODE_GENERATED
        ]
    
    async def handle(self, event: WebSocketEvent) -> bool:
        """Processa eventos de instância"""
        try:
            if event.type == EventType.INSTANCE_STATUS_CHANGED:
                return await self._handle_status_change(event)
            elif event.type == EventType.INSTANCE_CREATED:
                return await self._handle_instance_created(event)
            elif event.type == EventType.INSTANCE_DELETED:
                return await self._handle_instance_deleted(event)
            elif event.type == EventType.INSTANCE_CONNECTED:
                return await self._handle_instance_connected(event)
            elif event.type == EventType.INSTANCE_DISCONNECTED:
                return await self._handle_instance_disconnected(event)
            elif event.type == EventType.QR_CODE_GENERATED:
                return await self._handle_qr_code_generated(event)
            
            return False
            
        except Exception as e:
            self.logger.error(f"Erro no handler de instância: {e}")
            return False
    
    async def _handle_status_change(self, event: WebSocketEvent) -> bool:
        """Trata mudança de status da instância"""
        instance_id = event.data.get('instance_id')
        new_status = event.data.get('status')
        
        if not instance_id or not new_status:
            return False
        
        # Atualiza status local
        # TODO: Implementar atualização no store local
        
        # Broadcast para subscribers
        await self.websocket_manager.broadcast_event(
            event, SubscriptionType.INSTANCE_STATUS
        )
        
        self.logger.info(f"📱 Status da instância {instance_id} alterado para {new_status}")
        return True
    
    async def _handle_instance_created(self, event: WebSocketEvent) -> bool:
        """Trata criação de instância"""
        instance_data = event.data
        
        # Broadcast para todos os usuários autorizados
        await self.websocket_manager.broadcast_event(
            event, SubscriptionType.INSTANCE_STATUS
        )
        
        self.logger.info(f"📱 Nova instância criada: {instance_data.get('instance_name')}")
        return True
    
    async def _handle_instance_deleted(self, event: WebSocketEvent) -> bool:
        """Trata exclusão de instância"""
        instance_id = event.data.get('instance_id')
        
        # Broadcast para subscribers
        await self.websocket_manager.broadcast_event(
            event, SubscriptionType.INSTANCE_STATUS
        )
        
        self.logger.info(f"📱 Instância deletada: {instance_id}")
        return True
    
    async def _handle_instance_connected(self, event: WebSocketEvent) -> bool:
        """Trata conexão da instância"""
        instance_id = event.data.get('instance_id')
        
        # Broadcast para subscribers
        await self.websocket_manager.broadcast_event(
            event, SubscriptionType.INSTANCE_STATUS
        )
        
        self.logger.info(f"📱 Instância conectada: {instance_id}")
        return True
    
    async def _handle_instance_disconnected(self, event: WebSocketEvent) -> bool:
        """Trata desconexão da instância"""
        instance_id = event.data.get('instance_id')
        
        # Broadcast para subscribers
        await self.websocket_manager.broadcast_event(
            event, SubscriptionType.INSTANCE_STATUS
        )
        
        self.logger.warning(f"📱 Instância desconectada: {instance_id}")
        return True
    
    async def _handle_qr_code_generated(self, event: WebSocketEvent) -> bool:
        """Trata geração de QR code"""
        instance_id = event.data.get('instance_id')
        qr_code = event.data.get('qr_code')
        
        if not qr_code:
            return False
        
        # Broadcast apenas para usuários autorizados da instância
        await self.websocket_manager.broadcast_event(
            event, SubscriptionType.INSTANCE_STATUS
        )
        
        self.logger.info(f"📱 QR Code gerado para instância: {instance_id}")
        return True


class MessageEventHandler(EventHandler):
    """Handler para eventos de mensagens"""
    
    def __init__(self, websocket_manager: WebSocketManager, evolution_service: EvolutionService):
        super().__init__(websocket_manager)
        self.evolution_service = evolution_service
    
    @property
    def supported_events(self) -> List[EventType]:
        return [
            EventType.MESSAGE_RECEIVED,
            EventType.MESSAGE_SENT,
            EventType.MESSAGE_DELIVERED,
            EventType.MESSAGE_READ,
            EventType.MESSAGE_FAILED
        ]
    
    async def handle(self, event: WebSocketEvent) -> bool:
        """Processa eventos de mensagem"""
        try:
            if event.type == EventType.MESSAGE_RECEIVED:
                return await self._handle_message_received(event)
            elif event.type == EventType.MESSAGE_SENT:
                return await self._handle_message_sent(event)
            elif event.type == EventType.MESSAGE_DELIVERED:
                return await self._handle_message_delivered(event)
            elif event.type == EventType.MESSAGE_READ:
                return await self._handle_message_read(event)
            elif event.type == EventType.MESSAGE_FAILED:
                return await self._handle_message_failed(event)
            
            return False
            
        except Exception as e:
            self.logger.error(f"Erro no handler de mensagem: {e}")
            return False
    
    async def _handle_message_received(self, event: WebSocketEvent) -> bool:
        """Trata mensagem recebida"""
        message_data = event.data
        instance_id = message_data.get('instance_id')
        
        # Broadcast para subscribers de mensagens
        await self.websocket_manager.broadcast_event(
            event, SubscriptionType.MESSAGES
        )
        
        self.logger.info(f"💬 Mensagem recebida na instância {instance_id}")
        return True
    
    async def _handle_message_sent(self, event: WebSocketEvent) -> bool:
        """Trata mensagem enviada"""
        message_data = event.data
        instance_id = message_data.get('instance_id')
        
        # Broadcast para subscribers
        await self.websocket_manager.broadcast_event(
            event, SubscriptionType.MESSAGES
        )
        
        self.logger.info(f"💬 Mensagem enviada pela instância {instance_id}")
        return True
    
    async def _handle_message_delivered(self, event: WebSocketEvent) -> bool:
        """Trata confirmação de entrega"""
        message_id = event.data.get('message_id')
        
        # Broadcast para subscribers
        await self.websocket_manager.broadcast_event(
            event, SubscriptionType.MESSAGES
        )
        
        self.logger.debug(f"✅ Mensagem entregue: {message_id}")
        return True
    
    async def _handle_message_read(self, event: WebSocketEvent) -> bool:
        """Trata confirmação de leitura"""
        message_id = event.data.get('message_id')
        
        # Broadcast para subscribers
        await self.websocket_manager.broadcast_event(
            event, SubscriptionType.MESSAGES
        )
        
        self.logger.debug(f"👁️ Mensagem lida: {message_id}")
        return True
    
    async def _handle_message_failed(self, event: WebSocketEvent) -> bool:
        """Trata falha no envio"""
        message_id = event.data.get('message_id')
        error = event.data.get('error')
        
        # Broadcast para subscribers
        await self.websocket_manager.broadcast_event(
            event, SubscriptionType.MESSAGES
        )
        
        self.logger.error(f"❌ Falha no envio da mensagem {message_id}: {error}")
        return True


class AgentEventHandler(EventHandler):
    """Handler para eventos de agentes"""
    
    def __init__(self, websocket_manager: WebSocketManager, agno_service: AgnoService):
        super().__init__(websocket_manager)
        self.agno_service = agno_service
    
    @property
    def supported_events(self) -> List[EventType]:
        return [
            EventType.AGENT_CREATED,
            EventType.AGENT_UPDATED,
            EventType.AGENT_DELETED,
            EventType.AGENT_MATERIALIZED,
            EventType.AGENT_RESPONSE,
            EventType.AGENT_ERROR
        ]
    
    async def handle(self, event: WebSocketEvent) -> bool:
        """Processa eventos de agente"""
        try:
            if event.type == EventType.AGENT_CREATED:
                return await self._handle_agent_created(event)
            elif event.type == EventType.AGENT_UPDATED:
                return await self._handle_agent_updated(event)
            elif event.type == EventType.AGENT_DELETED:
                return await self._handle_agent_deleted(event)
            elif event.type == EventType.AGENT_MATERIALIZED:
                return await self._handle_agent_materialized(event)
            elif event.type == EventType.AGENT_RESPONSE:
                return await self._handle_agent_response(event)
            elif event.type == EventType.AGENT_ERROR:
                return await self._handle_agent_error(event)
            
            return False
            
        except Exception as e:
            self.logger.error(f"Erro no handler de agente: {e}")
            return False
    
    async def _handle_agent_created(self, event: WebSocketEvent) -> bool:
        """Trata criação de agente"""
        agent_data = event.data
        
        # Broadcast para subscribers de agentes
        await self.websocket_manager.broadcast_event(
            event, SubscriptionType.AGENT_EVENTS
        )
        
        self.logger.info(f"🤖 Agente criado: {agent_data.get('agent_name')}")
        return True
    
    async def _handle_agent_updated(self, event: WebSocketEvent) -> bool:
        """Trata atualização de agente"""
        agent_data = event.data
        
        # Broadcast para subscribers
        await self.websocket_manager.broadcast_event(
            event, SubscriptionType.AGENT_EVENTS
        )
        
        self.logger.info(f"🤖 Agente atualizado: {agent_data.get('agent_name')}")
        return True
    
    async def _handle_agent_deleted(self, event: WebSocketEvent) -> bool:
        """Trata exclusão de agente"""
        agent_data = event.data
        
        # Broadcast para subscribers
        await self.websocket_manager.broadcast_event(
            event, SubscriptionType.AGENT_EVENTS
        )
        
        self.logger.info(f"🤖 Agente deletado: {agent_data.get('agent_name')}")
        return True
    
    async def _handle_agent_materialized(self, event: WebSocketEvent) -> bool:
        """Trata materialização de agente"""
        agent_data = event.data
        
        # Broadcast para subscribers
        await self.websocket_manager.broadcast_event(
            event, SubscriptionType.AGENT_EVENTS
        )
        
        self.logger.info(f"🤖 Agente materializado: {agent_data.get('agent_name')}")
        return True
    
    async def _handle_agent_response(self, event: WebSocketEvent) -> bool:
        """Trata resposta de agente"""
        agent_data = event.data
        
        # Broadcast para subscribers
        await self.websocket_manager.broadcast_event(
            event, SubscriptionType.AGENT_EVENTS
        )
        
        self.logger.debug(f"🤖 Resposta do agente: {agent_data.get('agent_name')}")
        return True
    
    async def _handle_agent_error(self, event: WebSocketEvent) -> bool:
        """Trata erro de agente"""
        agent_data = event.data
        error = agent_data.get('error')
        
        # Broadcast para subscribers
        await self.websocket_manager.broadcast_event(
            event, SubscriptionType.AGENT_EVENTS
        )
        
        self.logger.error(f"🤖 Erro no agente {agent_data.get('agent_name')}: {error}")
        return True


class SystemEventHandler(EventHandler):
    """Handler para eventos do sistema"""
    
    @property
    def supported_events(self) -> List[EventType]:
        return [
            EventType.SYSTEM_STATUS,
            EventType.SYSTEM_ERROR,
            EventType.SYSTEM_MAINTENANCE,
            EventType.RATE_LIMIT_EXCEEDED,
            EventType.PERFORMANCE_METRICS,
            EventType.HEALTH_CHECK
        ]
    
    async def handle(self, event: WebSocketEvent) -> bool:
        """Processa eventos do sistema"""
        try:
            if event.type == EventType.SYSTEM_STATUS:
                return await self._handle_system_status(event)
            elif event.type == EventType.SYSTEM_ERROR:
                return await self._handle_system_error(event)
            elif event.type == EventType.SYSTEM_MAINTENANCE:
                return await self._handle_system_maintenance(event)
            elif event.type == EventType.RATE_LIMIT_EXCEEDED:
                return await self._handle_rate_limit_exceeded(event)
            elif event.type == EventType.PERFORMANCE_METRICS:
                return await self._handle_performance_metrics(event)
            elif event.type == EventType.HEALTH_CHECK:
                return await self._handle_health_check(event)
            
            return False
            
        except Exception as e:
            self.logger.error(f"Erro no handler do sistema: {e}")
            return False
    
    async def _handle_system_status(self, event: WebSocketEvent) -> bool:
        """Trata status do sistema"""
        # Broadcast para subscribers do sistema
        await self.websocket_manager.broadcast_event(
            event, SubscriptionType.SYSTEM_EVENTS
        )
        
        self.logger.info(f"⚙️ Status do sistema: {event.data.get('status')}")
        return True
    
    async def _handle_system_error(self, event: WebSocketEvent) -> bool:
        """Trata erro do sistema"""
        error_data = event.data
        
        # Broadcast para subscribers
        await self.websocket_manager.broadcast_event(
            event, SubscriptionType.SYSTEM_EVENTS
        )
        
        self.logger.error(f"⚙️ Erro do sistema: {error_data.get('message')}")
        return True
    
    async def _handle_system_maintenance(self, event: WebSocketEvent) -> bool:
        """Trata manutenção do sistema"""
        # Broadcast para todos os usuários
        await self.websocket_manager.broadcast_event(event)
        
        self.logger.warning(f"⚙️ Manutenção do sistema: {event.data.get('message')}")
        return True
    
    async def _handle_rate_limit_exceeded(self, event: WebSocketEvent) -> bool:
        """Trata excesso de rate limit"""
        user_id = event.data.get('user_id')
        
        # Envia apenas para o usuário específico
        if user_id:
            await self.websocket_manager.send_to_user(user_id, event)
        
        self.logger.warning(f"⚠️ Rate limit excedido para usuário: {user_id}")
        return True
    
    async def _handle_performance_metrics(self, event: WebSocketEvent) -> bool:
        """Trata métricas de performance"""
        # Broadcast apenas para admins
        # TODO: Implementar filtro por role
        await self.websocket_manager.broadcast_event(
            event, SubscriptionType.SYSTEM_EVENTS
        )
        
        self.logger.debug("📊 Métricas de performance enviadas")
        return True
    
    async def _handle_health_check(self, event: WebSocketEvent) -> bool:
        """Trata health check"""
        # Broadcast para subscribers
        await self.websocket_manager.broadcast_event(
            event, SubscriptionType.SYSTEM_EVENTS
        )
        
        self.logger.debug("❤️ Health check enviado")
        return True


class WebSocketHandlers:
    """
    Gerenciador de handlers WebSocket
    """
    
    def __init__(self, websocket_manager: WebSocketManager, 
                 evolution_service: Optional[EvolutionService] = None,
                 agno_service: Optional[AgnoService] = None):
        self.websocket_manager = websocket_manager
        self.handlers: Dict[EventType, EventHandler] = {}
        
        # Inicializa handlers
        self._setup_handlers(evolution_service, agno_service)
        
        # Estatísticas
        self.events_processed = 0
        self.events_failed = 0
        self.start_time = datetime.now(timezone.utc)
        
        logger.info("🎯 WebSocketHandlers inicializado")
    
    def _setup_handlers(self, evolution_service: Optional[EvolutionService],
                       agno_service: Optional[AgnoService]):
        """Configura handlers"""
        # Handler de instâncias
        if evolution_service:
            instance_handler = InstanceEventHandler(self.websocket_manager, evolution_service)
            for event_type in instance_handler.supported_events:
                self.handlers[event_type] = instance_handler
            
            # Handler de mensagens
            message_handler = MessageEventHandler(self.websocket_manager, evolution_service)
            for event_type in message_handler.supported_events:
                self.handlers[event_type] = message_handler
        
        # Handler de agentes
        if agno_service:
            agent_handler = AgentEventHandler(self.websocket_manager, agno_service)
            for event_type in agent_handler.supported_events:
                self.handlers[event_type] = agent_handler
        
        # Handler do sistema
        system_handler = SystemEventHandler(self.websocket_manager)
        for event_type in system_handler.supported_events:
            self.handlers[event_type] = system_handler
    
    async def process_event(self, event: WebSocketEvent) -> bool:
        """Processa um evento"""
        start_time = datetime.now(timezone.utc)
        
        try:
            handler = self.handlers.get(event.type)
            
            if not handler:
                logger.warning(f"Handler não encontrado para evento: {event.type}")
                return False
            
            # Processa evento
            success = await handler.handle(event)
            
            # Atualiza estatísticas
            if success:
                self.events_processed += 1
            else:
                self.events_failed += 1
            
            # Log de performance
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            if duration > 1.0:  # Log se demorar mais de 1 segundo
                logger.warning(f"Evento {event.type} demorou {duration:.2f}s para processar")
            
            return success
            
        except Exception as e:
            self.events_failed += 1
            logger.error(f"Erro ao processar evento {event.type}: {e}")
            return False
    
    def add_handler(self, event_type: EventType, handler: EventHandler):
        """Adiciona um handler customizado"""
        self.handlers[event_type] = handler
        logger.info(f"Handler adicionado para evento: {event_type}")
    
    def remove_handler(self, event_type: EventType):
        """Remove um handler"""
        if event_type in self.handlers:
            del self.handlers[event_type]
            logger.info(f"Handler removido para evento: {event_type}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas dos handlers"""
        uptime = (datetime.now(timezone.utc) - self.start_time).total_seconds()
        
        return {
            "events_processed": self.events_processed,
            "events_failed": self.events_failed,
            "success_rate": self.events_processed / (self.events_processed + self.events_failed) if (self.events_processed + self.events_failed) > 0 else 0,
            "events_per_second": self.events_processed / uptime if uptime > 0 else 0,
            "uptime_seconds": uptime,
            "registered_handlers": len(self.handlers),
            "handler_types": list(self.handlers.keys())
        }
    
    def list_handlers(self) -> Dict[str, str]:
        """Lista handlers registrados"""
        return {
            event_type.value: handler.__class__.__name__
            for event_type, handler in self.handlers.items()
        }


# Funções utilitárias para criar eventos comuns
async def emit_instance_status_change(websocket_manager: WebSocketManager,
                                     instance_id: str, instance_name: str,
                                     old_status: str, new_status: str):
    """Emite evento de mudança de status da instância"""
    event = create_instance_event(
        EventType.INSTANCE_STATUS_CHANGED,
        instance_id=instance_id,
        instance_name=instance_name,
        status=new_status,
        metadata={"old_status": old_status}
    )
    
    await websocket_manager.broadcast_event(event, SubscriptionType.INSTANCE_STATUS)


async def emit_message_received(websocket_manager: WebSocketManager,
                              message_id: str, instance_id: str,
                              from_number: str, content: str):
    """Emite evento de mensagem recebida"""
    event = create_message_event(
        EventType.MESSAGE_RECEIVED,
        message_id=message_id,
        instance_id=instance_id,
        from_number=from_number,
        content=content
    )
    
    await websocket_manager.broadcast_event(event, SubscriptionType.MESSAGES)


async def emit_agent_response(websocket_manager: WebSocketManager,
                            agent_id: str, agent_name: str,
                            response: str, execution_time: float):
    """Emite evento de resposta do agente"""
    event = create_agent_event(
        EventType.AGENT_RESPONSE,
        agent_id=agent_id,
        agent_name=agent_name,
        action="response",
        status="completed",
        response=response,
        execution_time=execution_time
    )
    
    await websocket_manager.broadcast_event(event, SubscriptionType.AGENT_EVENTS)


async def emit_system_error(websocket_manager: WebSocketManager,
                          component: str, error_message: str,
                          error_details: Optional[Dict[str, Any]] = None):
    """Emite evento de erro do sistema"""
    event = create_system_event(
        EventType.SYSTEM_ERROR,
        component=component,
        status="error",
        message=error_message,
        error=error_message,
        metrics=error_details or {}
    )
    
    await websocket_manager.broadcast_event(event, SubscriptionType.SYSTEM_EVENTS)


async def emit_performance_metrics(websocket_manager: WebSocketManager,
                                  cpu_usage: float, memory_usage: float,
                                  active_connections: int, requests_per_second: float,
                                  response_time_avg: float, error_rate: float):
    """Emite métricas de performance"""
    event = create_performance_event(
        cpu_usage=cpu_usage,
        memory_usage=memory_usage,
        active_connections=active_connections,
        requests_per_second=requests_per_second,
        response_time_avg=response_time_avg,
        error_rate=error_rate
    )
    
    await websocket_manager.broadcast_event(event, SubscriptionType.SYSTEM_EVENTS)
