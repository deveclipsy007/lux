"""
Sistema de Autenticação WebSocket para Evolution API

Implementa:
- Autenticação de tokens JWT
- Validação de API keys
- Controle de acesso por roles
- Rate limiting por usuário
- Auditoria de autenticação

Autor: AgnoMaster - Evolution API WebSocket Expert
Data: 2025-01-24
"""

import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, Set, List
from dataclasses import dataclass, field
from collections import defaultdict
import hashlib
import secrets

from loguru import logger
import redis.asyncio as redis
from jose import JWTError, jwt
from passlib.context import CryptContext

from ..auth.jwt_auth import JWTAuthenticator, User, Role
from ..auth.security_config import EvolutionSecuritySettings


@dataclass
class WebSocketSession:
    """Sessão WebSocket autenticada"""
    user: User
    connection_id: str
    authenticated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_activity: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    permissions: Set[str] = field(default_factory=set)
    metadata: Dict[str, any] = field(default_factory=dict)
    
    def update_activity(self):
        """Atualiza última atividade"""
        self.last_activity = datetime.now(timezone.utc)
    
    @property
    def session_duration(self) -> timedelta:
        return datetime.now(timezone.utc) - self.authenticated_at
    
    @property
    def idle_time(self) -> timedelta:
        return datetime.now(timezone.utc) - self.last_activity
    
    def has_permission(self, permission: str) -> bool:
        """Verifica se tem permissão"""
        return permission in self.permissions or "admin" in self.permissions
    
    def to_dict(self) -> Dict[str, any]:
        return {
            "user_id": self.user.id,
            "username": self.user.username,
            "connection_id": self.connection_id,
            "authenticated_at": self.authenticated_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "session_duration_seconds": self.session_duration.total_seconds(),
            "idle_time_seconds": self.idle_time.total_seconds(),
            "permissions": list(self.permissions),
            "metadata": self.metadata
        }


class WebSocketRateLimiter:
    """Rate limiter para WebSocket"""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client
        self.local_buckets: Dict[str, Dict[str, any]] = defaultdict(dict)
        self.cleanup_interval = 300  # 5 minutos
        self._cleanup_task = None
        
        if not redis_client:
            self._start_cleanup_task()
    
    async def is_allowed(self, user_id: str, action: str = "message", 
                        limit: int = 60, window: int = 60) -> bool:
        """Verifica se ação é permitida"""
        key = f"ws_rate_limit:{user_id}:{action}"
        now = datetime.now(timezone.utc)
        
        if self.redis_client:
            return await self._check_redis_rate_limit(key, limit, window, now)
        else:
            return await self._check_local_rate_limit(key, limit, window, now)
    
    async def _check_redis_rate_limit(self, key: str, limit: int, window: int, now: datetime) -> bool:
        """Verifica rate limit usando Redis"""
        try:
            pipe = self.redis_client.pipeline()
            pipe.zremrangebyscore(key, 0, now.timestamp() - window)
            pipe.zcard(key)
            pipe.zadd(key, {str(now.timestamp()): now.timestamp()})
            pipe.expire(key, window)
            
            results = await pipe.execute()
            current_count = results[1]
            
            return current_count < limit
        except Exception as e:
            logger.error(f"Erro no rate limiting Redis: {e}")
            return True  # Permite em caso de erro
    
    async def _check_local_rate_limit(self, key: str, limit: int, window: int, now: datetime) -> bool:
        """Verifica rate limit localmente"""
        if key not in self.local_buckets:
            self.local_buckets[key] = {"requests": [], "last_cleanup": now}
        
        bucket = self.local_buckets[key]
        cutoff_time = now - timedelta(seconds=window)
        
        # Remove requests antigas
        bucket["requests"] = [req_time for req_time in bucket["requests"] if req_time > cutoff_time]
        
        # Verifica limite
        if len(bucket["requests"]) >= limit:
            return False
        
        # Adiciona nova request
        bucket["requests"].append(now)
        bucket["last_cleanup"] = now
        
        return True
    
    def _start_cleanup_task(self):
        """Inicia task de limpeza"""
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    async def _cleanup_loop(self):
        """Loop de limpeza de buckets locais"""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self._cleanup_local_buckets()
            except Exception as e:
                logger.error(f"Erro na limpeza de rate limit: {e}")
    
    async def _cleanup_local_buckets(self):
        """Limpa buckets locais antigos"""
        now = datetime.now(timezone.utc)
        cutoff_time = now - timedelta(seconds=self.cleanup_interval)
        
        keys_to_remove = []
        for key, bucket in self.local_buckets.items():
            if bucket["last_cleanup"] < cutoff_time:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.local_buckets[key]
        
        if keys_to_remove:
            logger.debug(f"Limpeza rate limit: removidos {len(keys_to_remove)} buckets")


class WebSocketAuthenticator:
    """
    Autenticador WebSocket
    """
    
    def __init__(self, security_settings: Optional[EvolutionSecuritySettings] = None,
                 redis_client: Optional[redis.Redis] = None):
        self.settings = security_settings or EvolutionSecuritySettings()
        self.jwt_auth = JWTAuthenticator(self.settings)
        self.redis_client = redis_client
        self.rate_limiter = WebSocketRateLimiter(redis_client)
        
        # Sessões ativas
        self.active_sessions: Dict[str, WebSocketSession] = {}
        self.user_sessions: Dict[str, Set[str]] = defaultdict(set)
        
        # Permissões por role
        self.role_permissions = {
            Role.ADMIN: {
                "admin", "read", "write", "delete", "manage_instances",
                "send_messages", "view_logs", "manage_users", "system_control"
            },
            Role.USER: {
                "read", "write", "manage_instances", "send_messages"
            },
            Role.VIEWER: {
                "read", "view_logs"
            }
        }
        
        # Auditoria
        self.auth_attempts: List[Dict[str, any]] = []
        self.max_auth_attempts = 1000
        
        logger.info("🔐 WebSocketAuthenticator inicializado")
    
    async def authenticate(self, token: str, connection_id: str) -> User:
        """Autentica um token e cria sessão"""
        start_time = datetime.now(timezone.utc)
        
        try:
            # Valida token JWT
            user = await self.jwt_auth.verify_token(token)
            
            # Verifica rate limiting
            if not await self.rate_limiter.is_allowed(user.id, "auth", limit=10, window=60):
                raise ValueError("Rate limit de autenticação excedido")
            
            # Cria sessão
            session = await self._create_session(user, connection_id)
            
            # Log de auditoria
            await self._log_auth_attempt(
                user_id=user.id,
                username=user.username,
                connection_id=connection_id,
                success=True,
                duration=(datetime.now(timezone.utc) - start_time).total_seconds()
            )
            
            logger.info(f"🔐 Autenticação WebSocket bem-sucedida: {user.username} ({connection_id})")
            return user
            
        except Exception as e:
            # Log de auditoria para falha
            await self._log_auth_attempt(
                connection_id=connection_id,
                success=False,
                error=str(e),
                duration=(datetime.now(timezone.utc) - start_time).total_seconds()
            )
            
            logger.warning(f"🔐 Falha na autenticação WebSocket ({connection_id}): {e}")
            raise
    
    async def authenticate_api_key(self, api_key: str, connection_id: str) -> User:
        """Autentica usando API key"""
        try:
            user = await self.jwt_auth.verify_api_key(api_key)
            session = await self._create_session(user, connection_id)
            
            logger.info(f"🔑 Autenticação API key WebSocket: {user.username} ({connection_id})")
            return user
            
        except Exception as e:
            logger.warning(f"🔑 Falha na autenticação API key WebSocket ({connection_id}): {e}")
            raise
    
    async def _create_session(self, user: User, connection_id: str) -> WebSocketSession:
        """Cria uma nova sessão"""
        # Remove sessão existente se houver
        if connection_id in self.active_sessions:
            await self.remove_session(connection_id)
        
        # Cria nova sessão
        permissions = self.role_permissions.get(user.role, set())
        session = WebSocketSession(
            user=user,
            connection_id=connection_id,
            permissions=permissions
        )
        
        # Armazena sessão
        self.active_sessions[connection_id] = session
        self.user_sessions[user.id].add(connection_id)
        
        # Salva no Redis se disponível
        if self.redis_client:
            await self._save_session_to_redis(session)
        
        return session
    
    async def remove_session(self, connection_id: str):
        """Remove uma sessão"""
        if connection_id not in self.active_sessions:
            return
        
        session = self.active_sessions[connection_id]
        user_id = session.user.id
        
        # Remove das estruturas locais
        del self.active_sessions[connection_id]
        self.user_sessions[user_id].discard(connection_id)
        
        if not self.user_sessions[user_id]:
            del self.user_sessions[user_id]
        
        # Remove do Redis
        if self.redis_client:
            await self._remove_session_from_redis(connection_id)
        
        logger.debug(f"🔐 Sessão removida: {connection_id}")
    
    async def get_session(self, connection_id: str) -> Optional[WebSocketSession]:
        """Obtém uma sessão"""
        session = self.active_sessions.get(connection_id)
        
        if session:
            session.update_activity()
            
            # Atualiza no Redis
            if self.redis_client:
                await self._save_session_to_redis(session)
        
        return session
    
    async def verify_permission(self, connection_id: str, permission: str) -> bool:
        """Verifica se conexão tem permissão"""
        session = await self.get_session(connection_id)
        
        if not session:
            return False
        
        return session.has_permission(permission)
    
    async def check_rate_limit(self, connection_id: str, action: str = "message",
                              limit: int = 60, window: int = 60) -> bool:
        """Verifica rate limit para uma conexão"""
        session = await self.get_session(connection_id)
        
        if not session:
            return False
        
        return await self.rate_limiter.is_allowed(session.user.id, action, limit, window)
    
    async def get_user_sessions(self, user_id: str) -> List[WebSocketSession]:
        """Obtém todas as sessões de um usuário"""
        if user_id not in self.user_sessions:
            return []
        
        sessions = []
        for connection_id in self.user_sessions[user_id]:
            session = self.active_sessions.get(connection_id)
            if session:
                sessions.append(session)
        
        return sessions
    
    async def revoke_user_sessions(self, user_id: str) -> int:
        """Revoga todas as sessões de um usuário"""
        if user_id not in self.user_sessions:
            return 0
        
        connection_ids = list(self.user_sessions[user_id])
        
        for connection_id in connection_ids:
            await self.remove_session(connection_id)
        
        logger.info(f"🔐 Revogadas {len(connection_ids)} sessões do usuário {user_id}")
        return len(connection_ids)
    
    async def cleanup_expired_sessions(self, max_idle_time: int = 3600):
        """Limpa sessões expiradas"""
        now = datetime.now(timezone.utc)
        expired_sessions = []
        
        for connection_id, session in self.active_sessions.items():
            if session.idle_time.total_seconds() > max_idle_time:
                expired_sessions.append(connection_id)
        
        for connection_id in expired_sessions:
            await self.remove_session(connection_id)
        
        if expired_sessions:
            logger.info(f"🔐 Limpeza: removidas {len(expired_sessions)} sessões expiradas")
    
    async def _save_session_to_redis(self, session: WebSocketSession):
        """Salva sessão no Redis"""
        try:
            key = f"ws_session:{session.connection_id}"
            data = session.to_dict()
            await self.redis_client.setex(key, 3600, json.dumps(data))
        except Exception as e:
            logger.error(f"Erro ao salvar sessão no Redis: {e}")
    
    async def _remove_session_from_redis(self, connection_id: str):
        """Remove sessão do Redis"""
        try:
            key = f"ws_session:{connection_id}"
            await self.redis_client.delete(key)
        except Exception as e:
            logger.error(f"Erro ao remover sessão do Redis: {e}")
    
    async def _log_auth_attempt(self, connection_id: str, success: bool,
                               user_id: Optional[str] = None, username: Optional[str] = None,
                               error: Optional[str] = None, duration: float = 0):
        """Log de tentativa de autenticação"""
        attempt = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "connection_id": connection_id,
            "user_id": user_id,
            "username": username,
            "success": success,
            "error": error,
            "duration_seconds": duration
        }
        
        self.auth_attempts.append(attempt)
        
        # Mantém apenas os últimos N attempts
        if len(self.auth_attempts) > self.max_auth_attempts:
            self.auth_attempts = self.auth_attempts[-self.max_auth_attempts:]
        
        # Salva no Redis se disponível
        if self.redis_client:
            try:
                key = f"ws_auth_attempt:{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}:{connection_id}"
                await self.redis_client.setex(key, 86400, json.dumps(attempt))  # 24 horas
            except Exception as e:
                logger.error(f"Erro ao salvar log de autenticação: {e}")
    
    def get_auth_stats(self) -> Dict[str, any]:
        """Retorna estatísticas de autenticação"""
        total_attempts = len(self.auth_attempts)
        successful_attempts = sum(1 for attempt in self.auth_attempts if attempt["success"])
        failed_attempts = total_attempts - successful_attempts
        
        return {
            "active_sessions": len(self.active_sessions),
            "total_auth_attempts": total_attempts,
            "successful_attempts": successful_attempts,
            "failed_attempts": failed_attempts,
            "success_rate": successful_attempts / total_attempts if total_attempts > 0 else 0,
            "sessions_by_user": {
                user_id: len(connections)
                for user_id, connections in self.user_sessions.items()
            }
        }
    
    def get_session_info(self) -> List[Dict[str, any]]:
        """Retorna informações de todas as sessões"""
        return [session.to_dict() for session in self.active_sessions.values()]
