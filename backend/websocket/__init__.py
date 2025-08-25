"""
Sistema de WebSockets para Evolution API

Implementa comunicacao em tempo real para:
- Status de instancias WhatsApp
- Mensagens em tempo real
- Notificacoes de eventos
- Monitoramento de agentes
- Atualizacoes de sistema

Autor: AgnoMaster - Evolution API WebSocket Expert
Data: 2025-01-24
"""

try:
    from .simple_manager import SimpleConnectionManager
    from .websocket_handlers import WebSocketHandlers
    from .websocket_auth import WebSocketAuthenticator
    from .websocket_events import EventType, WebSocketEvent
    
    __all__ = [
        'SimpleConnectionManager',
        'WebSocketHandlers', 
        'WebSocketAuthenticator',
        'EventType',
        'WebSocketEvent'
    ]
except ImportError:
    # Fallback if some modules have encoding issues
    from .simple_manager import SimpleConnectionManager
    __all__ = ['SimpleConnectionManager']