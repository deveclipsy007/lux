"""
Serviço de integração com Evolution API para WhatsApp

Este serviço fornece um cliente completo para interação com a Evolution API,
permitindo criar instâncias, gerenciar conexões, enviar mensagens e
configurar webhooks para receber mensagens do WhatsApp.

Funcionalidades:
- Criação e gerenciamento de instâncias WhatsApp
- Geração e monitoramento de QR Codes
- Envio de mensagens (texto, mídia)
- Configuração de webhooks
- Monitoramento de status de conexão
- Tratamento de erros e retry automático

Documentação da Evolution API: https://evolution-api.com/docs

Autor: Agno SDK Agent Generator
Data: 2025-01-24
"""

import asyncio
import base64
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Callable
from pathlib import Path
import mimetypes
import aiofiles

import httpx
from loguru import logger
try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings

from models import Message, ConnectionState, MessageType
from backend.db.whatsapp_instance_repository import WhatsAppInstanceRepository
from backend.db.message_repository import MessageRepository

class EvolutionAPIError(Exception):
    """Exceção personalizada para erros da Evolution API"""
    
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict] = None):
        self.message = message
        self.status_code = status_code
        self.response_data = response_data or {}
        super().__init__(self.message)

class EvolutionService:
    """
    Cliente para Evolution API com funcionalidades completas para WhatsApp
    """
    
    def __init__(self, settings):
        self.settings = settings
        self.base_url = settings.evolution_base_url.rstrip('/')
        self.api_key = settings.evolution_api_key
        
        # Configurações do cliente HTTP
        self.timeout = httpx.Timeout(30.0, connect=10.0)
        self.retry_attempts = 3
        self.retry_delay = 2.0
        
        # Map between Evolution instance names and database IDs
        self._instance_ids: Dict[str, int] = {}

        # Repositories
        self.instance_repo = WhatsAppInstanceRepository()
        self.message_repo = MessageRepository()
        
        # Callbacks para eventos
        self._message_callbacks: List[Callable] = []
        self._status_callbacks: List[Callable] = []
        
        logger.info(f"📱 EvolutionService inicializado - Base URL: {self.base_url}")
    
    @property
    def headers(self) -> Dict[str, str]:
        """Headers padrão para requisições"""
        return {
            "apikey": self.api_key,
            "Content-Type": "application/json",
            "User-Agent": "Agno-SDK-Agent-Generator/1.0"
        }
    
    # OPERAÇÕES BÁSICAS COM HTTP CLIENT
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        retry_count: int = 0
    ) -> Dict[str, Any]:
        """
        Realiza requisição HTTP com retry automático e tratamento de erros
        
        Args:
            method: Método HTTP (GET, POST, PUT, DELETE)
            endpoint: Endpoint da API (sem base URL)
            data: Dados JSON para enviar
            params: Parâmetros de query string
            files: Arquivos para upload
            retry_count: Contador interno de tentativas
            
        Returns:
            Dict com resposta da API
            
        Raises:
            EvolutionAPIError: Em caso de erro na API
        """
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                
                # Prepara dados da requisição
                request_kwargs = {
                    "headers": self.headers,
                    "params": params
                }
                
                if files:
                    # Para upload de arquivos, remove Content-Type do header
                    headers = self.headers.copy()
                    del headers["Content-Type"]
                    request_kwargs["headers"] = headers
                    request_kwargs["files"] = files
                    
                    if data:
                        request_kwargs["data"] = data
                else:
                    # Para JSON, usa json parameter
                    if data:
                        request_kwargs["json"] = data
                
                # Log da requisição (sem dados sensíveis)
                logger.debug(f"🌐 {method} {endpoint} - Tentativa {retry_count + 1}")
                
                # Executa requisição
                response = await client.request(method, url, **request_kwargs)
                
                # Log da resposta
                logger.debug(f"📡 {response.status_code} {endpoint} - {response.elapsed.total_seconds():.2f}s")
                
                # Tenta parsear JSON da resposta
                try:
                    response_data = response.json()
                except json.JSONDecodeError:
                    response_data = {"raw_response": response.text}
                
                # Verifica se foi sucesso
                if response.is_success:
                    return response_data
                
                # Trata erros HTTP
                error_message = self._extract_error_message(response_data, response.status_code)
                
                # Retry para erros temporários
                if self._should_retry(response.status_code) and retry_count < self.retry_attempts:
                    await asyncio.sleep(self.retry_delay * (retry_count + 1))
                    return await self._make_request(method, endpoint, data, params, files, retry_count + 1)
                
                # Lança exceção para erros definitivos
                raise EvolutionAPIError(
                    message=error_message,
                    status_code=response.status_code,
                    response_data=response_data
                )
                
        except httpx.RequestError as e:
            error_msg = f"Erro de conexão com Evolution API: {str(e)}"
            
            # Retry para erros de conexão
            if retry_count < self.retry_attempts:
                logger.warning(f"⚠️ {error_msg} - Tentativa {retry_count + 1}/{self.retry_attempts}")
                await asyncio.sleep(self.retry_delay * (retry_count + 1))
                return await self._make_request(method, endpoint, data, params, files, retry_count + 1)
            
            logger.error(f"❌ {error_msg} - Esgotadas tentativas")
            raise EvolutionAPIError(error_msg)
        
        except Exception as e:
            error_msg = f"Erro inesperado na requisição: {str(e)}"
            logger.error(f"💥 {error_msg}")
            logger.debug(f"🔍 Detalhes completos do erro: {e}")
            raise EvolutionAPIError(error_msg)
    
    def _extract_error_message(self, response_data: Dict[str, Any], status_code: int) -> str:
        """Extrai mensagem de erro da resposta da API"""
        
        # Tenta diferentes campos comuns de erro
        for field in ['message', 'error', 'detail', 'msg']:
            if field in response_data:
                return str(response_data[field])
        
        # Mensagens padrão baseadas no status code
        status_messages = {
            400: "Requisição inválida - verifique os dados enviados",
            401: "Não autorizado - verifique a API key",
            403: "Acesso negado - permissões insuficientes",
            404: "Recurso não encontrado",
            429: "Muitas requisições - tente novamente em alguns segundos",
            500: "Erro interno do servidor Evolution API",
            502: "Bad Gateway - Evolution API temporariamente indisponível",
            503: "Serviço indisponível - Evolution API fora do ar"
        }
        
        return status_messages.get(status_code, f"Erro HTTP {status_code}")
    
    def _should_retry(self, status_code: int) -> bool:
        """Determina se deve tentar novamente baseado no status code"""
        
        # Retry apenas para erros temporários
        retry_codes = [429, 500, 502, 503, 504]
        return status_code in retry_codes
    
    # OPERAÇÕES DE INSTÂNCIA
    
    async def create_instance(self, instance_name: str, webhook_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Cria ou recupera uma instância do WhatsApp
        
        Args:
            instance_name: Nome único da instância
            webhook_url: URL para receber webhooks (opcional)
            
        Returns:
            Dict com dados da instância criada
        """
        
        logger.info(f"📱 Criando instância: {instance_name}")
        
        try:
            # Dados para criação da instância
            payload = {
                "instanceName": instance_name,
                "integration": "WHATSAPP-BAILEYS",
                "webhook_url": webhook_url
            }

            # Remove campos None
            payload = {k: v for k, v in payload.items() if v is not None}

            # Cria instância via API
            response = await self._make_request("POST", "/instance/create", data=payload)

            # Persiste registro da instância no banco
            db_instance = await self.instance_repo.create_instance(
                {
                    "agentId": 1,
                    "status": ConnectionState.DISCONNECTED.value,
                    "qrCode": None,
                    "phoneNumber": None,
                }
            )
            self._instance_ids[instance_name] = int(db_instance["id"])

            logger.info(f"✅ Instância {instance_name} criada com sucesso")

            return {
                "instance_id": instance_name,
                "status": "created",
                "webhook_url": webhook_url,
                "api_response": response
            }

        except EvolutionAPIError as e:
            logger.error(f"❌ Erro ao criar instância {instance_name}: {e.message}")

            if e.status_code in (409, 500):
                logger.warning(
                    f"Instância {instance_name} pode já existir ou estar inconsistente: {e.status_code}"
                )
                # Tenta recuperar estado atual da instância
                try:
                    status_info = await self.get_instance_status(instance_name)
                    logger.info(f"🔄 Instância {instance_name} já existente recuperada")
                    return {
                        "instance_id": instance_name,
                        "status": status_info.get("state", "unknown"),
                        "webhook_url": webhook_url,
                        "api_response": status_info,
                    }
                except EvolutionAPIError as status_error:
                    logger.warning(
                        f"⚠️ Não foi possível obter status da instância {instance_name}: {status_error.message}"
                    )
                    # Tenta remover e recriar instância
                    try:
                        logger.info(f"🗑️ Removendo instância {instance_name} para recriação")
                        await self.delete_instance(instance_name)
                        response = await self._make_request(
                            "POST", "/instance/create", data=payload
                        )

                        db_instance = await self.instance_repo.create_instance(
                            {
                                "agentId": 1,
                                "status": ConnectionState.DISCONNECTED.value,
                                "qrCode": None,
                                "phoneNumber": None,
                            }
                        )
                        self._instance_ids[instance_name] = int(db_instance["id"])
                        logger.info(
                            f"✅ Instância {instance_name} recriada com sucesso"
                        )
                        return {
                            "instance_id": instance_name,
                            "status": "recreated",
                            "webhook_url": webhook_url,
                            "api_response": response,
                        }
                    except EvolutionAPIError as recreate_error:
                        error_msg = (
                            f"Falha ao recriar instância {instance_name}: {recreate_error.message}"
                        )
                        logger.error(f"❌ {error_msg}")
                        raise EvolutionAPIError(
                            error_msg,
                            recreate_error.status_code,
                            recreate_error.response_data,
                        )

            # Se não for caso tratado, propaga erro original
            raise
    
    async def get_instance_info(self, instance_name: str) -> Dict[str, Any]:
        """
        Obtém informações detalhadas de uma instância
        
        Args:
            instance_name: Nome da instância
            
        Returns:
            Dict com informações da instância
        """
        
        try:
            response = await self._make_request("GET", f"/instance/fetchInstances/{instance_name}")
            
            logger.debug(f"📋 Informações da instância {instance_name} obtidas")
            
            return response
            
        except EvolutionAPIError as e:
            logger.error(f"❌ Erro ao obter info da instância {instance_name}: {e.message}")
            raise

    async def get_instance_status(self, instance_name: str) -> Dict[str, Any]:
        """Obtém estado atual de conexão da instância"""

        return await self.get_connection_state(instance_name)

    async def delete_instance(self, instance_name: str) -> bool:
        """
        Exclui uma instância
        
        Args:
            instance_name: Nome da instância
            
        Returns:
            True se excluída com sucesso
        """
        
        try:
            await self._make_request("DELETE", f"/instance/delete/{instance_name}")
            
            # Remove mapeamento da instância
            if instance_name in self._instance_ids:
                del self._instance_ids[instance_name]
            
            logger.info(f"🗑️ Instância {instance_name} excluída")
            return True
            
        except EvolutionAPIError as e:
            logger.error(f"❌ Erro ao excluir instância {instance_name}: {e.message}")
            return False
    
    # OPERAÇÕES DE CONEXÃO E QR CODE
    
    async def get_qr_code(self, instance_name: str) -> Optional[Dict[str, Any]]:
        """
        Obtém QR Code para pareamento
        
        Args:
            instance_name: Nome da instância
            
        Returns:
            Dict com QR Code em base64 ou None se não disponível
        """
        
        logger.info(f"📱 Obtendo QR Code para {instance_name}")
        
        try:
            response = await self._make_request("GET", f"/instance/connect/{instance_name}")
            
            # Verifica se tem QR Code na resposta
            qr_code = None
            qr_expires_at = None
            
            # Debug: vamos ver o que a API está retornando
            logger.debug(f"🔍 Resposta do /instance/connect: {json.dumps(response, indent=2)}")
            
            if "qrcode" in response:
                qr_code = response["qrcode"]["code"]
                # QR Code expira em 60 segundos por padrão
                qr_expires_at = datetime.now() + timedelta(seconds=60)
            elif "qr" in response:
                qr_code = response["qr"]
                qr_expires_at = datetime.now() + timedelta(seconds=60)
            elif "base64" in response:
                qr_code = response["base64"]
                qr_expires_at = datetime.now() + timedelta(seconds=60)
            
            if qr_code:
                instance_id = self._instance_ids.get(instance_name)
                if instance_id:
                    await self.instance_repo.update_instance(
                        instance_id, {"qrCode": qr_code}
                    )
                logger.info(f"✅ QR Code gerado para {instance_name}")

                return {
                    "qr": qr_code,
                    "expires_at": qr_expires_at.isoformat() if qr_expires_at else None,
                    "status": "QR_AVAILABLE"
                }
            else:
                logger.warning(f"⚠️ QR Code não disponível para {instance_name}")
                return None
                
        except EvolutionAPIError as e:
            logger.error(f"❌ Erro ao obter QR Code {instance_name}: {e.message}")
            return None
    
    async def get_connection_state(self, instance_name: str) -> Dict[str, Any]:
        """
        Verifica estado de conexão da instância
        
        Args:
            instance_name: Nome da instância
            
        Returns:
            Dict com estado da conexão
        """
        
        try:
            response = await self._make_request("GET", f"/instance/connectionState/{instance_name}")
            
            # Debug: vamos ver o que a API está retornando
            logger.debug(f"🔍 Resposta do /instance/connectionState: {json.dumps(response, indent=2)}")
            
            # Mapeia estados da Evolution API para nossos estados
            state_map = {
                "close": ConnectionState.DISCONNECTED,
                "connecting": ConnectionState.CONNECTING,
                "open": ConnectionState.CONNECTED
            }
            
            # A API retorna estado dentro de response["instance"]["state"]  
            if "instance" in response:
                api_state = response["instance"].get("state", "close")
            else:
                api_state = response.get("state", "close")
                
            our_state = state_map.get(api_state, ConnectionState.DISCONNECTED)
            
            instance_id = self._instance_ids.get(instance_name)
            if instance_id:
                update_data: Dict[str, Any] = {"status": our_state.value}
                if our_state == ConnectionState.CONNECTED:
                    update_data["qrCode"] = None
                await self.instance_repo.update_instance(instance_id, update_data)
            
            logger.debug(f"🔍 Estado de {instance_name}: {our_state}")
            
            return {
                "state": our_state,
                "api_state": api_state,
                "instance_id": instance_name,
                "raw_response": response
            }
            
        except EvolutionAPIError as e:
            logger.error(f"❌ Erro ao verificar estado {instance_name}: {e.message}")
            return {
                "state": ConnectionState.ERROR,
                "instance_id": instance_name,
                "error": e.message
            }
    
    async def disconnect_instance(self, instance_name: str) -> bool:
        """
        Desconecta uma instância do WhatsApp
        
        Args:
            instance_name: Nome da instância
            
        Returns:
            True se desconectada com sucesso
        """
        
        try:
            await self._make_request("DELETE", f"/instance/logout/{instance_name}")

            instance_id = self._instance_ids.get(instance_name)
            if instance_id:
                await self.instance_repo.update_instance(
                    instance_id, {"status": ConnectionState.DISCONNECTED.value}
                )

            logger.info(f"📱 Instância {instance_name} desconectada")
            return True
            
        except EvolutionAPIError as e:
            logger.error(f"❌ Erro ao desconectar {instance_name}: {e.message}")
            return False
    
    # ENVIO DE MENSAGENS
    
    async def send_text_message(self, instance_name: str, to: str, message: str) -> Dict[str, Any]:
        """
        Envia mensagem de texto
        
        Args:
            instance_name: Nome da instância
            to: Número do destinatário (formato internacional)
            message: Texto da mensagem
            
        Returns:
            Dict com dados da mensagem enviada
        """
        
        logger.info(f"💬 Enviando mensagem texto: {instance_name} -> {to}")
        
        try:
            payload = {
                "number": to,
                "text": message
            }
            
            response = await self._make_request(
                "POST",
                f"/message/sendText/{instance_name}",
                data=payload
            )
            
            instance_id = self._instance_ids.get(instance_name)
            if instance_id:
                await self.message_repo.log_message(
                    {
                        "instanceId": instance_id,
                        "agentId": 1,
                        "fromNumber": None,
                        "toNumber": to,
                        "content": message,
                    }
                )
            
            logger.info(f"✅ Mensagem enviada - ID: {response.get('message_id', 'N/A')}")
            
            return {
                "message_id": response.get("key", {}).get("id"),
                "status": "sent",
                "timestamp": datetime.now().isoformat(),
                "to": to,
                "api_response": response
            }
            
        except EvolutionAPIError as e:
            logger.error(f"❌ Erro ao enviar mensagem para {to}: {e.message}")
            raise
    
    async def send_media_message(
        self,
        instance_name: str,
        to: str,
        media_url: str,
        caption: Optional[str] = None,
        media_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Envia mensagem com mídia (imagem, vídeo, áudio, documento)
        
        Args:
            instance_name: Nome da instância
            to: Número do destinatário
            media_url: URL da mídia ou caminho do arquivo local
            caption: Legenda opcional
            media_type: Tipo da mídia (image, video, audio, document)
            
        Returns:
            Dict com dados da mensagem enviada
        """
        
        logger.info(f"📎 Enviando mídia: {instance_name} -> {to}")
        
        try:
            # Detecta tipo de mídia se não fornecido
            if not media_type:
                media_type = self._detect_media_type(media_url)
            
            # Prepara payload baseado no tipo
            payload = {
                "number": to,
            }
            
            if media_type == "image":
                payload["mediaMessage"] = {
                    "media": media_url,
                    "caption": caption or ""
                }
                endpoint = f"/message/sendImage/{instance_name}"
            elif media_type == "video":
                payload["mediaMessage"] = {
                    "media": media_url,
                    "caption": caption or ""
                }
                endpoint = f"/message/sendVideo/{instance_name}"
            elif media_type == "audio":
                payload["mediaMessage"] = {
                    "media": media_url
                }
                endpoint = f"/message/sendAudio/{instance_name}"
            elif media_type == "document":
                payload["mediaMessage"] = {
                    "media": media_url,
                    "fileName": Path(media_url).name,
                    "caption": caption or ""
                }
                endpoint = f"/message/sendDocument/{instance_name}"
            else:
                raise EvolutionAPIError(f"Tipo de mídia não suportado: {media_type}")
            
            response = await self._make_request("POST", endpoint, data=payload)

            instance_id = self._instance_ids.get(instance_name)
            if instance_id:
                await self.message_repo.log_message(
                    {
                        "instanceId": instance_id,
                        "agentId": 1,
                        "fromNumber": None,
                        "toNumber": to,
                        "content": caption or f"Mídia: {media_type}",
                    }
                )

            logger.info(f"✅ Mídia enviada - Tipo: {media_type}")

            return {
                "message_id": response.get("key", {}).get("id"),
                "status": "sent",
                "media_type": media_type,
                "timestamp": datetime.now().isoformat(),
                "api_response": response
            }
            
        except EvolutionAPIError as e:
            logger.error(f"❌ Erro ao enviar mídia para {to}: {e.message}")
            raise
    
    def _detect_media_type(self, media_path: str) -> str:
        """
        Detecta tipo de mídia baseado na extensão do arquivo
        
        Args:
            media_path: Caminho ou URL da mídia
            
        Returns:
            Tipo da mídia (image, video, audio, document)
        """
        
        # Obtém tipo MIME
        mime_type, _ = mimetypes.guess_type(media_path)
        
        if not mime_type:
            return "document"
        
        if mime_type.startswith("image/"):
            return "image"
        elif mime_type.startswith("video/"):
            return "video"
        elif mime_type.startswith("audio/"):
            return "audio"
        else:
            return "document"
    
    # CONFIGURAÇÃO DE WEBHOOKS
    
    async def set_webhook(self, instance_name: str, webhook_url: str, events: Optional[List[str]] = None) -> bool:
        """
        Configura webhook para receber eventos
        
        Args:
            instance_name: Nome da instância
            webhook_url: URL para receber os webhooks
            events: Lista de eventos para escutar
            
        Returns:
            True se configurado com sucesso
        """
        
        if events is None:
            events = [
                "QRCODE_UPDATED",
                "MESSAGES_UPSERT", 
                "MESSAGES_UPDATE",
                "SEND_MESSAGE",
                "CONNECTION_UPDATE"
            ]
        
        logger.info(f"🔗 Configurando webhook para {instance_name}: {webhook_url}")
        
        try:
            # Usando apenas URL básica para testar
            payload = {
                "url": webhook_url
            }
            
            logger.debug(f"🔍 Payload webhook: {json.dumps(payload, indent=2)}")
            
            result = await self._make_request(
                "POST",
                f"/webhook/set/{instance_name}",
                data=payload
            )
            
            logger.debug(f"🔍 Resposta webhook: {json.dumps(result, indent=2)}")
            
            logger.info(f"✅ Webhook configurado para {instance_name}")
            return True
            
        except EvolutionAPIError as e:
            logger.error(f"❌ Erro ao configurar webhook {instance_name}: {e.message}")
            return False
    
    async def remove_webhook(self, instance_name: str) -> bool:
        """
        Remove configuração de webhook
        
        Args:
            instance_name: Nome da instância
            
        Returns:
            True se removido com sucesso
        """
        
        try:
            await self._make_request("DELETE", f"/webhook/unset/{instance_name}")
            
            logger.info(f"🔗 Webhook removido de {instance_name}")
            return True
            
        except EvolutionAPIError as e:
            logger.error(f"❌ Erro ao remover webhook {instance_name}: {e.message}")
            return False
    
    # PROCESSAMENTO DE WEBHOOKS RECEBIDOS
    
    def process_webhook_payload(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Processa payload recebido via webhook
        
        Args:
            payload: Dados do webhook
            
        Returns:
            Dict com dados processados ou None se ignorado
        """
        
        try:
            event_type = payload.get("type", "unknown")
            instance_name = payload.get("instance", "")
            
            logger.debug(f"📨 Webhook recebido: {event_type} de {instance_name}")
            
            if event_type == "messages.upsert":
                return self._process_message_webhook(payload)
            elif event_type == "connection.update":
                return self._process_connection_webhook(payload)
            else:
                logger.debug(f"⚠️ Tipo de webhook ignorado: {event_type}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Erro ao processar webhook: {e}")
            return None
    
    def _process_message_webhook(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Processa webhook de mensagem recebida"""
        
        try:
            instance_name = payload.get("instance", "")
            messages_data = payload.get("data", {}).get("messages", [])
            
            processed_messages = []
            
            for msg_data in messages_data:
                # Extrai dados da mensagem
                key = msg_data.get("key", {})
                message_content = msg_data.get("message", {})
                
                # Ignora mensagens enviadas por nós
                if key.get("fromMe", False):
                    continue
                
                # Cria objeto da mensagem
                msg = Message(
                    id=key.get("id", ""),
                    instance_id=instance_name,
                    from_number=key.get("remoteJid", "").replace("@s.whatsapp.net", ""),
                    from_me=False,
                    message_type=MessageType.TEXT,  # Simplificado por agora
                    content=self._extract_message_text(message_content),
                    timestamp=datetime.fromtimestamp(msg_data.get("messageTimestamp", 0))
                )
                
                processed_messages.append(msg)

                instance_id = self._instance_ids.get(instance_name)
                if instance_id:
                    asyncio.create_task(
                        self.message_repo.log_message(
                            {
                                "instanceId": instance_id,
                                "agentId": 1,
                                "fromNumber": msg.from_number,
                                "toNumber": None,
                                "content": msg.content,
                            }
                        )
                    )
            
            # Chama callbacks registrados
            for callback in self._message_callbacks:
                try:
                    asyncio.create_task(callback(processed_messages))
                except Exception as e:
                    logger.error(f"❌ Erro em callback de mensagem: {e}")
            
            return {
                "type": "messages",
                "instance": instance_name,
                "messages": [msg.to_dict() for msg in processed_messages]
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao processar webhook de mensagem: {e}")
            return None
    
    def _process_connection_webhook(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Processa webhook de mudança de conexão"""
        
        try:
            instance_name = payload.get("instance", "")
            connection_data = payload.get("data", {})
            
            new_state = connection_data.get("state", "unknown")
            
            # Mapeia estado
            state_map = {
                "close": ConnectionState.DISCONNECTED,
                "connecting": ConnectionState.CONNECTING,
                "open": ConnectionState.CONNECTED
            }
            
            our_state = state_map.get(new_state, ConnectionState.DISCONNECTED)
            
            instance_id = self._instance_ids.get(instance_name)
            old_state = None
            if instance_id:
                asyncio.create_task(
                    self.instance_repo.update_instance(
                        instance_id, {"status": our_state.value}
                    )
                )
                logger.info(f"🔄 Estado de {instance_name}: {our_state}")
            
            # Chama callbacks de status
            for callback in self._status_callbacks:
                try:
                    asyncio.create_task(callback(instance_name, our_state))
                except Exception as e:
                    logger.error(f"❌ Erro em callback de status: {e}")
            
            return {
                "type": "connection",
                "instance": instance_name,
                "old_state": old_state if 'old_state' in locals() else None,
                "new_state": our_state
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao processar webhook de conexão: {e}")
            return None
    
    def _extract_message_text(self, message_content: Dict[str, Any]) -> str:
        """Extrai texto da mensagem do payload do WhatsApp"""
        
        # Tenta diferentes campos onde o texto pode estar
        if "conversation" in message_content:
            return message_content["conversation"]
        elif "extendedTextMessage" in message_content:
            return message_content["extendedTextMessage"].get("text", "")
        elif "imageMessage" in message_content:
            return message_content["imageMessage"].get("caption", "[Imagem]")
        elif "videoMessage" in message_content:
            return message_content["videoMessage"].get("caption", "[Vídeo]")
        elif "audioMessage" in message_content:
            return "[Áudio]"
        elif "documentMessage" in message_content:
            return f"[Documento: {message_content['documentMessage'].get('fileName', 'arquivo')}]"
        else:
            return "[Mensagem não suportada]"
    
    # CALLBACKS E EVENTOS
    
    def add_message_callback(self, callback: Callable[[List[Message]], None]):
        """
        Adiciona callback para mensagens recebidas
        
        Args:
            callback: Função async que recebe lista de mensagens
        """
        self._message_callbacks.append(callback)
        logger.debug("📥 Callback de mensagem adicionado")
    
    def add_status_callback(self, callback: Callable[[str, ConnectionState], None]):
        """
        Adiciona callback para mudanças de status
        
        Args:
            callback: Função async que recebe (instance_name, new_state)
        """
        self._status_callbacks.append(callback)
        logger.debug("📊 Callback de status adicionado")
    
    def remove_message_callback(self, callback: Callable):
        """Remove callback de mensagem"""
        if callback in self._message_callbacks:
            self._message_callbacks.remove(callback)
    
    def remove_status_callback(self, callback: Callable):
        """Remove callback de status"""
        if callback in self._status_callbacks:
            self._status_callbacks.remove(callback)
    
    # UTILITÁRIOS E MONITORAMENTO
    
    async def test_connection(self) -> bool:
        """
        Testa conectividade com a Evolution API
        
        Returns:
            True se conectividade OK
        """
        
        try:
            # Tenta fazer uma requisição simples
            await self._make_request("GET", "/instance/fetchInstances", params={"limit": 1})
            logger.info("✅ Conexão com Evolution API OK")
            return True
            
        except Exception as e:
            logger.error(f"❌ Falha na conexão com Evolution API: {e}")
            return False
    
    async def get_instance_list(self) -> List[Dict[str, Any]]:
        """
        Lista todas as instâncias
        
        Returns:
            Lista de instâncias
        """
        
        try:
            response = await self._make_request("GET", "/instance/fetchInstances")
            
            instances = response if isinstance(response, list) else response.get("instances", [])
            
            logger.debug(f"📋 {len(instances)} instâncias encontradas")
            return instances
            
        except Exception as e:
            logger.error(f"❌ Erro ao listar instâncias: {e}")
            return []
    
    # Alias para compatibilidade
    async def list_instances(self) -> List[Dict[str, Any]]:
        """Alias para get_instance_list"""
        return await self.get_instance_list()

    def get_cached_instance(self, instance_name: str) -> Optional[int]:
        """Retorna o ID da instância armazenado em memória."""
        return self._instance_ids.get(instance_name)
    
    async def get_health_status(self) -> Dict[str, Any]:
        """
        Obtém status de saúde do serviço
        
        Returns:
            Dict com métricas de saúde
        """
        
        try:
            connection_ok = await self.test_connection()
            total_instances = len(self._instance_ids)
            return {
                "evolution_api_connected": connection_ok,
                "total_cached_instances": total_instances,
                "connected_instances": total_instances,
                "active_qr_codes": 0,
                "message_callbacks": len(self._message_callbacks),
                "status_callbacks": len(self._status_callbacks),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter status de saúde: {e}")
            return {
                "evolution_api_connected": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }