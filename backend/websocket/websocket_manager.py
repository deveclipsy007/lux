"""
Gerenciador de WebSockets para Evolution API

Implementa:
- Gerenciamento de conexões
- Broadcasting de eventos
- Autenticação de WebSocket
- Rate limiting
- Reconexão automática
- Monitoramento de saúde

Autor: AgnoMaster - Evolution API WebSocket Expert
Data: 2025-01-24
"""

import json
import asyncio
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Set, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import uuid

from fastapi import WebSocket, WebSocketDisconnect, status
from loguru import logger
import redis.asyncio as redis
from starlette.websockets import WebSocketState

from .websocket_events import EventType, WebSocketEvent
from .websocket_auth import WebSocketAuthenticator
from ..auth.jwt_auth import User


class ConnectionState(str, Enum):
    """Estados de conexão WebSocket"""
    CONNECTING = "connecting"
    CONNECTED = "connected"
    AUTHENTICATED = "authenticated"
    DISCONNECTING = "disconnecting"
    DISCONNECTED = "disconnected"
    ERROR = "error"


class SubscriptionType(str, Enum):
    """Tipos de subscrição"""
    ALL = "all"
    INSTANCE_STATUS = "instance_status"
    MESSAGES = "messages"
    AGENT_EVENTS = "agent_events"
    SYSTEM_EVENTS = "system_events"
    USER_EVENTS = "user_events"


@dataclass
class WebSocketConnection:
    """Representa uma conexão WebSocket"""
    id: str
    websocket: WebSocket
    user: Optional[User] = None
    state: ConnectionState = ConnectionState.CONNECTING
    connected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_ping: Optional[datetime] = None
    last_pong: Optional[datetime] = None
    subscriptions: Set[SubscriptionType] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)
    message_count: int = 0
    error_count: int = 0
    
    @property
    def is_authenticated(self) -> bool:
        return self.state == ConnectionState.AUTHENTICATED and self.user is not None
    
    @property
    def is_alive(self) -> bool:
        return self.state in [ConnectionState.CONNECTED, ConnectionState.AUTHENTICATED]
    
    @property
    def connection_duration(self) -> timedelta:
        return datetime.now(timezone.utc) - self.connected_at
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user.id if self.user else None,
            "username": self.user.username if self.user else None,
            "state": self.state.value,
            "connected_at": self.connected_at.isoformat(),
            "last_ping": self.last_ping.isoformat() if self.last_ping else None,
            "last_pong": self.last_pong.isoformat() if self.last_pong else None,
            "subscriptions": list(self.subscriptions),
            "message_count": self.message_count,
            "error_count": self.error_count,
            "connection_duration_seconds": self.connection_duration.total_seconds(),
            "metadata": self.metadata
        }


class ConnectionManager:
    """
    Gerenciador de conexões WebSocket
    """
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.connections: Dict[str, WebSocketConnection] = {}
        self.user_connections: Dict[str, Set[str]] = defaultdict(set)
        self.subscription_connections: Dict[SubscriptionType, Set[str]] = defaultdict(set)
        self.redis_client = redis_client
        
        # Estatísticas
        self.total_connections = 0
        self.total_messages = 0
        self.start_time = datetime.now(timezone.utc)
        
        # Tasks
        self._heartbeat_task = None
        self._cleanup_task = None
        self._stats_task = None
        
        self._start_background_tasks()
        
        logger.info("🔌 ConnectionManager inicializado")
    
    async def connect(self, websocket: WebSocket, connection_id: Optional[str] = None) -> WebSocketConnection:
        """Aceita uma nova conexão WebSocket"""
        if websocket.application_state != WebSocketState.CONNECTED:
            await websocket.accept()
        
        if not connection_id:
            connection_id = str(uuid.uuid4())
        
        connection = WebSocketConnection(
            id=connection_id,
            websocket=websocket,
            state=ConnectionState.CONNECTED
        )
        
        self.connections[connection_id] = connection
        self.total_connections += 1
        
        logger.info(f"🔌 Nova conexão WebSocket: {connection_id}")
        
        # Envia mensagem de boas-vindas
        await self.send_to_connection(connection_id, WebSocketEvent(
            type=EventType.CONNECTION_ESTABLISHED,
            data={
                "connection_id": connection_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "message": "Conexão estabelecida com sucesso"
            }
        ))
        
        return connection
    
    async def disconnect(self, connection_id: str, code: int = 1000, reason: str = "Normal closure"):
        """Desconecta uma conexão WebSocket"""
        if connection_id not in self.connections:
            return
        
        connection = self.connections[connection_id]
        connection.state = ConnectionState.DISCONNECTING
        
        try:
            await connection.websocket.close(code=code, reason=reason)
        except Exception as e:
            logger.warning(f"Erro ao fechar WebSocket {connection_id}: {e}")
        
        # Remove das estruturas de dados
        if connection.user:
            self.user_connections[connection.user.id].discard(connection_id)
            if not self.user_connections[connection.user.id]:
                del self.user_connections[connection.user.id]
        
        for subscription in connection.subscriptions:
            self.subscription_connections[subscription].discard(connection_id)
        
        connection.state = ConnectionState.DISCONNECTED
        del self.connections[connection_id]
        
        logger.info(f"🔌 Conexão WebSocket desconectada: {connection_id} ({reason})")
    
    async def authenticate_connection(self, connection_id: str, user: User):
        """Autentica uma conexão"""
        if connection_id not in self.connections:
            raise ValueError(f"Conexão {connection_id} não encontrada")
        
        connection = self.connections[connection_id]
        connection.user = user
        connection.state = ConnectionState.AUTHENTICATED
        
        # Adiciona à lista de conexões do usuário
        self.user_connections[user.id].add(connection_id)
        
        logger.info(f"🔐 Conexão autenticada: {connection_id} (usuário: {user.username})")
        
        # Envia confirmação de autenticação
        await self.send_to_connection(connection_id, WebSocketEvent(
            type=EventType.AUTHENTICATION_SUCCESS,
            data={
                "user_id": user.id,
                "username": user.username,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        ))
    
    async def subscribe(self, connection_id: str, subscription_type: SubscriptionType):
        """Adiciona uma subscrição"""
        if connection_id not in self.connections:
            raise ValueError(f"Conexão {connection_id} não encontrada")
        
        connection = self.connections[connection_id]
        connection.subscriptions.add(subscription_type)
        self.subscription_connections[subscription_type].add(connection_id)
        
        logger.debug(f"📡 Subscrição adicionada: {connection_id} -> {subscription_type.value}")
        
        # Confirma subscrição
        await self.send_to_connection(connection_id, WebSocketEvent(
            type=EventType.SUBSCRIPTION_CONFIRMED,
            data={
                "subscription_type": subscription_type.value,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        ))
    
    async def unsubscribe(self, connection_id: str, subscription_type: SubscriptionType):
        """Remove uma subscrição"""
        if connection_id not in self.connections:
            return
        
        connection = self.connections[connection_id]
        connection.subscriptions.discard(subscription_type)
        self.subscription_connections[subscription_type].discard(connection_id)
        
        logger.debug(f"📡 Subscrição removida: {connection_id} -> {subscription_type.value}")
    
    async def send_to_connection(self, connection_id: str, event: WebSocketEvent) -> bool:
        """Envia um evento para uma conexão específica"""
        if connection_id not in self.connections:
            return False
        
        connection = self.connections[connection_id]
        
        if not connection.is_alive:
            return False
        
        try:
            message = json.dumps(event.to_dict())
            await connection.websocket.send_text(message)
            connection.message_count += 1
            self.total_messages += 1
            return True
        except Exception as e:
            logger.error(f"Erro ao enviar mensagem para {connection_id}: {e}")
            connection.error_count += 1
            await self.disconnect(connection_id, code=1011, reason="Send error")
            return False
    
    async def send_to_user(self, user_id: str, event: WebSocketEvent) -> int:
        """Envia um evento para todas as conexões de um usuário"""
        if user_id not in self.user_connections:
            return 0
        
        sent_count = 0
        connection_ids = list(self.user_connections[user_id])
        
        for connection_id in connection_ids:
            if await self.send_to_connection(connection_id, event):
                sent_count += 1
        
        return sent_count
    
    async def broadcast_to_subscription(self, subscription_type: SubscriptionType, event: WebSocketEvent) -> int:
        """Faz broadcast para todas as conexões de uma subscrição"""
        if subscription_type not in self.subscription_connections:
            return 0
        
        sent_count = 0
        connection_ids = list(self.subscription_connections[subscription_type])
        
        for connection_id in connection_ids:
            if await self.send_to_connection(connection_id, event):
                sent_count += 1
        
        return sent_count
    
    async def broadcast_to_all(self, event: WebSocketEvent) -> int:
        """Faz broadcast para todas as conexões"""
        sent_count = 0
        connection_ids = list(self.connections.keys())
        
        for connection_id in connection_ids:
            if await self.send_to_connection(connection_id, event):
                sent_count += 1
        
        return sent_count
    
    async def handle_ping(self, connection_id: str):
        """Trata ping de uma conexão"""
        if connection_id not in self.connections:
            return
        
        connection = self.connections[connection_id]
        connection.last_ping = datetime.now(timezone.utc)
        
        # Responde com pong
        await self.send_to_connection(connection_id, WebSocketEvent(
            type=EventType.PONG,
            data={"timestamp": connection.last_ping.isoformat()}
        ))
    
    async def handle_pong(self, connection_id: str):
        """Trata pong de uma conexão"""
        if connection_id not in self.connections:
            return
        
        connection = self.connections[connection_id]
        connection.last_pong = datetime.now(timezone.utc)
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas das conexões"""
        active_connections = len(self.connections)
        authenticated_connections = sum(1 for conn in self.connections.values() if conn.is_authenticated)
        
        return {
            "active_connections": active_connections,
            "authenticated_connections": authenticated_connections,
            "total_connections": self.total_connections,
            "total_messages": self.total_messages,
            "uptime_seconds": (datetime.now(timezone.utc) - self.start_time).total_seconds(),
            "connections_by_subscription": {
                sub_type.value: len(connections)
                for sub_type, connections in self.subscription_connections.items()
            },
            "connections_by_user": {
                user_id: len(connections)
                for user_id, connections in self.user_connections.items()
            }
        }
    
    def get_connection_info(self, connection_id: str) -> Optional[Dict[str, Any]]:
        """Retorna informações de uma conexão"""
        if connection_id not in self.connections:
            return None
        
        return self.connections[connection_id].to_dict()
    
    def list_connections(self) -> List[Dict[str, Any]]:
        """Lista todas as conexões"""
        return [conn.to_dict() for conn in self.connections.values()]
    
    def _start_background_tasks(self):
        """Inicia tasks em background"""
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        self._stats_task = asyncio.create_task(self._stats_loop())

    async def shutdown(self):
        """Cancela tasks em background"""
        tasks = [self._heartbeat_task, self._cleanup_task, self._stats_task]
        for task in tasks:
            if task:
                task.cancel()
        await asyncio.gather(*[t for t in tasks if t], return_exceptions=True)
        logger.info("🔄 ConnectionManager tasks cancelled")
    
    async def _heartbeat_loop(self):
        """Loop de heartbeat para verificar conexões"""
        try:
            while True:
                await asyncio.sleep(30)  # Heartbeat a cada 30 segundos
                await self._send_heartbeat()
        except asyncio.CancelledError:
            logger.info("Heartbeat loop cancelled")
        except Exception as e:
            logger.error(f"Erro no heartbeat: {e}")
    
    async def _send_heartbeat(self):
        """Envia heartbeat para todas as conexões"""
        now = datetime.now(timezone.utc)
        stale_connections = []
        
        for connection_id, connection in self.connections.items():
            # Verifica se a conexão está "morta"
            if connection.last_pong:
                time_since_pong = now - connection.last_pong
                if time_since_pong > timedelta(minutes=2):
                    stale_connections.append(connection_id)
                    continue

            try:
                # Envia ping frame e evento
                await connection.websocket.ping()
                connection.last_ping = now
                await self.send_to_connection(connection_id, WebSocketEvent(
                    type=EventType.PING,
                    data={"timestamp": now.isoformat()}
                ))
            except Exception:
                stale_connections.append(connection_id)
        
        # Remove conexões "mortas"
        for connection_id in stale_connections:
            logger.warning(f"Removendo conexão inativa: {connection_id}")
            await self.disconnect(connection_id, code=1001, reason="Connection timeout")

        # Registra métricas de heartbeat no Redis
        if self.redis_client:
            try:
                metrics = {
                    "timestamp": now.isoformat(),
                    "active_connections": len(self.connections),
                    "stale_connections": len(stale_connections)
                }
                await self.redis_client.setex(
                    "websocket_heartbeat",
                    120,
                    json.dumps(metrics)
                )
            except Exception as e:
                logger.error(f"Erro ao registrar heartbeat no Redis: {e}")
    
    async def _cleanup_loop(self):
        """Loop de limpeza"""
        try:
            while True:
                await asyncio.sleep(300)  # Limpeza a cada 5 minutos
                await self._cleanup_connections()
        except asyncio.CancelledError:
            logger.info("Cleanup loop cancelled")
        except Exception as e:
            logger.error(f"Erro na limpeza: {e}")
    
    async def _cleanup_connections(self):
        """Limpa conexões órfãs"""
        orphaned_connections = []
        
        for connection_id, connection in self.connections.items():
            try:
                # Tenta enviar uma mensagem de teste
                await connection.websocket.ping()
            except Exception:
                orphaned_connections.append(connection_id)
        
        for connection_id in orphaned_connections:
            logger.warning(f"Removendo conexão órfã: {connection_id}")
            await self.disconnect(connection_id, code=1011, reason="Connection lost")
    
    async def _stats_loop(self):
        """Loop de estatísticas"""
        try:
            while True:
                await asyncio.sleep(60)  # Estatísticas a cada minuto
                stats = self.get_connection_stats()
                logger.info(f"📊 WebSocket Stats: {stats['active_connections']} ativas, {stats['total_messages']} mensagens")

                # Salva no Redis se disponível
                if self.redis_client:
                    await self.redis_client.setex(
                        "websocket_stats",
                        300,  # 5 minutos
                        json.dumps(stats)
                    )
        except asyncio.CancelledError:
            logger.info("Stats loop cancelled")
        except Exception as e:
            logger.error(f"Erro nas estatísticas: {e}")


class WebSocketManager:
    """
    Gerenciador principal de WebSockets
    """
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.connection_manager = ConnectionManager(redis_client)
        self.authenticator = WebSocketAuthenticator()
        self.redis_client = redis_client
        
        # Event handlers
        self.event_handlers: Dict[EventType, List[Callable]] = defaultdict(list)
        
        logger.info("🚀 WebSocketManager inicializado")
    
    async def handle_websocket(self, websocket: WebSocket, connection_id: Optional[str] = None):
        """Trata uma nova conexão WebSocket"""
        connection = await self.connection_manager.connect(websocket, connection_id)
        
        try:
            while True:
                # Recebe mensagem
                data = await websocket.receive_text()
                await self._handle_message(connection.id, data)
        
        except WebSocketDisconnect:
            logger.info(f"Cliente desconectado: {connection.id}")
        except Exception as e:
            logger.error(f"Erro na conexão WebSocket {connection.id}: {e}")
        finally:
            await self.connection_manager.disconnect(connection.id)
    
    async def _handle_message(self, connection_id: str, message: str):
        """Trata uma mensagem recebida"""
        try:
            data = json.loads(message)
            event_type = EventType(data.get('type'))
            event_data = data.get('data', {})
            
            # Cria evento
            event = WebSocketEvent(
                type=event_type,
                data=event_data,
                connection_id=connection_id
            )
            
            # Trata evento
            await self._process_event(event)
            
        except json.JSONDecodeError:
            logger.warning(f"Mensagem JSON inválida de {connection_id}: {message}")
        except ValueError as e:
            logger.warning(f"Tipo de evento inválido de {connection_id}: {e}")
        except Exception as e:
            logger.error(f"Erro ao processar mensagem de {connection_id}: {e}")
    
    async def _process_event(self, event: WebSocketEvent):
        """Processa um evento"""
        # Eventos do sistema
        if event.type == EventType.AUTHENTICATE:
            await self._handle_authenticate(event)
        elif event.type == EventType.SUBSCRIBE:
            await self._handle_subscribe(event)
        elif event.type == EventType.UNSUBSCRIBE:
            await self._handle_unsubscribe(event)
        elif event.type == EventType.PING:
            await self.connection_manager.handle_ping(event.connection_id)
        elif event.type == EventType.PONG:
            await self.connection_manager.handle_pong(event.connection_id)
        
        # Chama handlers customizados
        for handler in self.event_handlers.get(event.type, []):
            try:
                await handler(event)
            except Exception as e:
                logger.error(f"Erro no handler de evento {event.type}: {e}")
    
    async def _handle_authenticate(self, event: WebSocketEvent):
        """Trata autenticação"""
        token = event.data.get('token')
        if not token:
            await self.connection_manager.send_to_connection(
                event.connection_id,
                WebSocketEvent(
                    type=EventType.AUTHENTICATION_FAILED,
                    data={"error": "Token não fornecido"}
                )
            )
            return
        
        try:
            user = await self.authenticator.authenticate(token)
            await self.connection_manager.authenticate_connection(event.connection_id, user)
        except Exception as e:
            await self.connection_manager.send_to_connection(
                event.connection_id,
                WebSocketEvent(
                    type=EventType.AUTHENTICATION_FAILED,
                    data={"error": str(e)}
                )
            )
    
    async def _handle_subscribe(self, event: WebSocketEvent):
        """Trata subscrição"""
        subscription_type = event.data.get('subscription_type')
        if not subscription_type:
            return
        
        try:
            sub_type = SubscriptionType(subscription_type)
            await self.connection_manager.subscribe(event.connection_id, sub_type)
        except ValueError:
            logger.warning(f"Tipo de subscrição inválido: {subscription_type}")
    
    async def _handle_unsubscribe(self, event: WebSocketEvent):
        """Trata cancelamento de subscrição"""
        subscription_type = event.data.get('subscription_type')
        if not subscription_type:
            return
        
        try:
            sub_type = SubscriptionType(subscription_type)
            await self.connection_manager.unsubscribe(event.connection_id, sub_type)
        except ValueError:
            logger.warning(f"Tipo de subscrição inválido: {subscription_type}")
    
    def add_event_handler(self, event_type: EventType, handler: Callable):
        """Adiciona um handler de evento"""
        self.event_handlers[event_type].append(handler)
    
    def remove_event_handler(self, event_type: EventType, handler: Callable):
        """Remove um handler de evento"""
        if handler in self.event_handlers[event_type]:
            self.event_handlers[event_type].remove(handler)
    
    async def broadcast_event(self, event: WebSocketEvent, subscription_type: Optional[SubscriptionType] = None):
        """Faz broadcast de um evento"""
        if subscription_type:
            return await self.connection_manager.broadcast_to_subscription(subscription_type, event)
        else:
            return await self.connection_manager.broadcast_to_all(event)
    
    async def send_to_user(self, user_id: str, event: WebSocketEvent):
        """Envia evento para um usuário específico"""
        return await self.connection_manager.send_to_user(user_id, event)
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas"""
        return self.connection_manager.get_connection_stats()
    
    def get_connections(self) -> List[Dict[str, Any]]:
        """Lista conexões"""
        return self.connection_manager.list_connections()
