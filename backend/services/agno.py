"""
Serviço de integração com o framework Agno

Este serviço fornece utilitários e helpers para criação, configuração
e execução de agentes utilizando o framework Agno.

Funcionalidades:
- Criação de configurações de agentes baseadas na especialização
- Templates de instruções por tipo de agente
- Integração com ferramentas/tools específicas
- Helpers para execução e monitoramento

Autor: Agno SDK Agent Generator
Data: 2025-01-24
"""

import os
import asyncio
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable, Union
from pathlib import Path
from enum import Enum

from loguru import logger
try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings

from schemas import AgentCreate, AgentSpecialization, AgentTool

class AgnoService:
    """
    Serviço principal para integração com framework Agno
    """
    
    def __init__(self, settings):
        self.settings = settings
        self.model_provider = settings.agno_model_provider
        self.model_name = settings.agno_model_name
        
        # Cache de templates e configurações
        self._templates_cache: Dict[str, Any] = {}
        self._tool_configs: Dict[str, Any] = {}
        
        logger.info(f"🤖 AgnoService inicializado - Provider: {self.model_provider}, Model: {self.model_name}")
    
    # TEMPLATES DE INSTRUÇÕES POR ESPECIALIZAÇÃO
    
    def get_specialization_template(self, specialization: AgentSpecialization) -> Dict[str, Any]:
        """
        Obtém template de configuração baseado na especialização
        
        Args:
            specialization: Tipo de especialização do agente
            
        Returns:
            Dict com configurações padrão para a especialização
        """
        
        templates = {
            AgentSpecialization.ATENDIMENTO: {
                "base_instructions": """Você é um assistente especializado em atendimento ao cliente. 

Suas responsabilidades principais:
- Responder dúvidas de forma clara e educada
- Resolver problemas dos clientes de forma eficiente  
- Coletar informações necessárias quando preciso
- Escalar para humanos quando necessário
- Manter histórico das interações

Diretrizes de comportamento:
- Sempre seja educado, prestativo e empático
- Use linguagem clara e acessível
- Confirme o entendimento antes de prosseguir
- Ofereça alternativas quando possível
- Mantenha foco na resolução do problema""",
                
                "suggested_tools": ["whatsapp", "email"],
                "conversation_starters": [
                    "Olá! Como posso ajudá-lo hoje?",
                    "Boa tarde! Em que posso ser útil?", 
                    "Seja bem-vindo! Como posso auxiliá-lo?"
                ],
                "escalation_keywords": [
                    "falar com humano", "atendente", "gerente", 
                    "reclamação", "cancelar", "estou irritado"
                ],
                "max_conversation_length": 20,
                "response_style": "formal_friendly"
            },
            
            AgentSpecialization.VENDAS: {
                "base_instructions": """Você é um assistente especializado em vendas e conversão.

Suas responsabilidades principais:
- Apresentar produtos/serviços de forma atrativa
- Qualificar leads e identificar necessidades
- Conduzir o processo de vendas até o fechamento
- Lidar com objeções de forma construtiva
- Acompanhar pós-venda

Diretrizes de comportamento:
- Seja consultivo, não apenas vendedor
- Escute ativamente as necessidades do cliente
- Use técnicas de storytelling para engajar
- Crie senso de urgência quando apropriado
- Sempre adicione valor nas interações""",
                
                "suggested_tools": ["whatsapp", "crm", "payments"],
                "conversation_starters": [
                    "Olá! Vi seu interesse em nossos produtos. Como posso ajudar?",
                    "Boa tarde! Que tal conhecer nossa solução ideal para você?",
                    "Seja bem-vindo! Vou te ajudar a encontrar exatamente o que precisa!"
                ],
                "sales_funnel_stages": [
                    "awareness", "interest", "consideration", "intent", "purchase", "retention"
                ],
                "objection_handlers": {
                    "preço": "Entendo sua preocupação com o investimento. Vamos analisar o retorno...",
                    "tempo": "Sei que tempo é valioso. Nossa solução vai otimizar exatamente isso...",
                    "concorrência": "Ótima pergunta! O diferencial da nossa solução é..."
                },
                "max_conversation_length": 30,
                "response_style": "persuasive_friendly"
            },
            
            AgentSpecialization.AGENDAMENTO: {
                "base_instructions": """Você é um assistente especializado em agendamentos e reservas.

Suas responsabilidades principais:
- Verificar disponibilidade de horários
- Agendar, reagendar e cancelar compromissos
- Enviar lembretes e confirmações
- Gerenciar lista de espera
- Otimizar ocupação da agenda

Diretrizes de comportamento:
- Seja preciso com datas, horários e informações
- Confirme todos os detalhes antes de finalizar
- Ofereça alternativas quando horário não disponível  
- Mantenha comunicação proativa sobre mudanças
- Facilite o processo para o cliente""",
                
                "suggested_tools": ["whatsapp", "calendar", "email"],
                "conversation_starters": [
                    "Olá! Vou te ajudar a agendar seu horário. Qual o melhor dia para você?",
                    "Boa tarde! Para qual serviço gostaria de agendar?",
                    "Seja bem-vindo! Vamos encontrar o horário perfeito para você!"
                ],
                "time_slots": {
                    "morning": "08:00-12:00",
                    "afternoon": "13:00-17:00", 
                    "evening": "18:00-22:00"
                },
                "booking_fields": [
                    "service_type", "date", "time", "duration", "contact", "notes"
                ],
                "reminder_schedule": ["24h", "2h", "30min"],
                "max_conversation_length": 15,
                "response_style": "efficient_friendly"
            },
            
            AgentSpecialization.SUPORTE: {
                "base_instructions": """Você é um assistente especializado em suporte técnico.

Suas responsabilidades principais:
- Diagnosticar problemas técnicos
- Fornecer soluções passo-a-passo
- Criar tickets de suporte quando necessário
- Acompanhar resolução de issues
- Documentar soluções para knowledge base

Diretrizes de comportamento:
- Seja técnico mas acessível na linguagem
- Faça perguntas específicas para diagnóstico
- Forneça instruções claras e detalhadas
- Teste soluções com o cliente
- Documente problemas recorrentes""",
                
                "suggested_tools": ["whatsapp", "email", "database"],
                "conversation_starters": [
                    "Olá! Vou te ajudar a resolver esse problema técnico. Pode me descrever o que está acontecendo?",
                    "Boa tarde! Qual dificuldade técnica posso ajudar você a resolver?",
                    "Seja bem-vindo ao suporte! Vamos resolver isso juntos!"
                ],
                "diagnostic_questions": [
                    "Quando o problema começou a acontecer?",
                    "Que mensagem de erro aparece?",
                    "Já tentou reiniciar o sistema?",
                    "Qual sistema operacional está usando?"
                ],
                "severity_levels": ["baixa", "média", "alta", "crítica"],
                "max_conversation_length": 25,
                "response_style": "technical_helpful"
            },
            
            AgentSpecialization.CUSTOM: {
                "base_instructions": """Você é um assistente personalizado configurado para atender necessidades específicas.

Suas responsabilidades serão definidas pelas instruções customizadas fornecidas.

Diretrizes gerais:
- Siga exatamente as instruções personalizadas
- Mantenha consistência no comportamento
- Adapte-se ao contexto específico
- Priorize a experiência do usuário""",
                
                "suggested_tools": ["whatsapp"],
                "conversation_starters": [
                    "Olá! Como posso ajudá-lo?"
                ],
                "max_conversation_length": 20,
                "response_style": "adaptive"
            }
        }
        
        return templates.get(specialization, templates[AgentSpecialization.CUSTOM])
    
    def build_agent_instructions(self, agent_data: AgentCreate) -> str:
        """
        Constrói instruções completas do agente combinando template e customizações
        
        Args:
            agent_data: Dados do agente criado pelo usuário
            
        Returns:
            String com instruções completas do agente
        """
        
        template = self.get_specialization_template(agent_data.specialization)
        base_instructions = template["base_instructions"]
        
        # Combina instruções base com customizações do usuário
        full_instructions = f"""{base_instructions}

## Instruções Personalizadas

{agent_data.instructions}

## Ferramentas Disponíveis

Você tem acesso às seguintes ferramentas:
{self._format_tools_list(agent_data.tools)}

## Configurações do Agente

- Nome: {agent_data.agent_name}
- Especialização: {agent_data.specialization}
- Ferramentas: {', '.join(agent_data.tools)}

Lembre-se de sempre manter o foco em sua especialização e usar as ferramentas disponíveis de forma eficiente."""

        return full_instructions
    
    def _format_tools_list(self, tools: List[str]) -> str:
        """Formata lista de ferramentas para as instruções"""
        
        tool_descriptions = {
            "whatsapp": "- WhatsApp: Envio e recebimento de mensagens via WhatsApp",
            "email": "- E-mail: Envio de e-mails e notificações",
            "calendar": "- Calendário: Agendamento e gerenciamento de compromissos",
            "webhooks": "- Webhooks: Integração com APIs externas via HTTP",
            "database": "- Banco de dados: Consulta e armazenamento de informações"
        }
        
        formatted = []
        for tool in tools:
            if tool in tool_descriptions:
                formatted.append(tool_descriptions[tool])
        
        return "\n".join(formatted) if formatted else "- Nenhuma ferramenta específica configurada"
    
    # CONFIGURAÇÃO DE TOOLS/INTEGRAÇÕES
    
    def get_tool_config(self, tool: AgentTool, agent_name: str) -> Dict[str, Any]:
        """
        Gera configuração específica para uma ferramenta
        
        Args:
            tool: Tipo da ferramenta
            agent_name: Nome do agente (usado em configurações)
            
        Returns:
            Dict com configuração da ferramenta
        """
        
        configs = {
            AgentTool.WHATSAPP: {
                "instance_name": f"{agent_name}-whatsapp",
                "webhook_url": f"/webhook/whatsapp/{agent_name}",
                "auto_reply": True,
                "message_delay": 1.0,
                "typing_indicator": True,
                "read_receipts": True,
                "max_message_length": 4096
            },
            
            AgentTool.EMAIL: {
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "use_tls": True,
                "from_name": f"Agente {agent_name}",
                "signature": f"\n\n---\nMensagem automática do agente {agent_name}\nGerado por Agno SDK Agent Generator",
                "max_attachments": 5,
                "attachment_size_limit": "10MB"
            },
            
            AgentTool.CALENDAR: {
                "calendar_provider": "google",
                "timezone": "America/Sao_Paulo",
                "working_hours": {
                    "start": "09:00",
                    "end": "18:00",
                    "days": ["monday", "tuesday", "wednesday", "thursday", "friday"]
                },
                "booking_buffer": 30,  # minutos entre agendamentos
                "advance_booking_days": 30,
                "reminder_times": [1440, 60]  # minutos antes do compromisso
            },
            
            AgentTool.WEBHOOKS: {
                "timeout": 30,
                "retry_attempts": 3,
                "retry_delay": 5,
                "headers": {
                    "User-Agent": f"Agno-Agent-{agent_name}/1.0",
                    "Content-Type": "application/json"
                },
                "allowed_methods": ["GET", "POST", "PUT", "PATCH"],
                "max_payload_size": "1MB"
            },
            
            AgentTool.DATABASE: {
                "database_type": "sqlite",
                "database_file": f"agents/{agent_name}/data.db",
                "connection_pool_size": 5,
                "query_timeout": 30,
                "auto_backup": True,
                "backup_frequency": "daily",
                "tables": {
                    "conversations": {
                        "id": "INTEGER PRIMARY KEY",
                        "contact": "TEXT",
                        "started_at": "TIMESTAMP",
                        "last_message": "TIMESTAMP",
                        "status": "TEXT"
                    },
                    "messages": {
                        "id": "INTEGER PRIMARY KEY",
                        "conversation_id": "INTEGER",
                        "content": "TEXT",
                        "sender": "TEXT",
                        "timestamp": "TIMESTAMP"
                    }
                }
            }
        }
        
        return configs.get(tool, {})
    
    # GERAÇÃO DE CÓDIGO AGNO
    
    def generate_agent_class(self, agent_data: AgentCreate) -> str:
        """
        Gera código da classe do agente Agno
        
        Args:
            agent_data: Dados do agente
            
        Returns:
            String com código Python da classe do agente
        """
        
        class_name = self._to_class_name(agent_data.agent_name)
        instructions = self.build_agent_instructions(agent_data)
        
        # Imports baseados nas tools
        imports = self._generate_imports(agent_data.tools)
        
        # Métodos baseados na especialização
        methods = self._generate_specialized_methods(agent_data.specialization)
        
        # Configuração das tools
        tool_setup = self._generate_tool_setup(agent_data.tools, agent_data.agent_name)
        
        code = f'''"""
Agente {agent_data.agent_name}
Especialização: {agent_data.specialization}

Gerado automaticamente pelo Agno SDK Agent Generator
"""

{imports}

class {class_name}(BaseAgent):
    """
    Agente especializado em {agent_data.specialization}
    
    Ferramentas: {', '.join(agent_data.tools)}
    """
    
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        
        # Configurações específicas
        self.specialization = "{agent_data.specialization}"
        self.tools = {agent_data.tools}
        
        # Templates da especialização
        self.template = self._load_specialization_template()
        
        # Configuração das ferramentas
        self._setup_tools()
        
        logger.info(f"🤖 Agente {self.config.name} inicializado - {self.specialization}")
    
    def _load_specialization_template(self, agent_data: AgentCreate) -> Dict[str, Any]:
        """Carrega template da especialização"""
        specialization = getattr(AgentSpecialization, agent_data.specialization.upper())
        return self.get_specialization_template(specialization)
    
    def _setup_tools(self):
        """Configura ferramentas disponíveis"""
        pass  # Implementação das ferramentas
    
    async def process_message(self, message: str, context: Dict[str, Any] = None) -> str:
        """
        Processa mensagem recebida
        
        Args:
            message: Mensagem recebida
            context: Contexto da conversa
            
        Returns:
            Resposta do agente
        """
        try:
            logger.debug(f"Processando mensagem: {{message[:100]}}...")
            
            # Enriquece contexto com dados da especialização
            enriched_context = self._enrich_context(context or {{}})
            
            # Processa baseado na especialização
            response = await self._process_by_specialization(message, enriched_context)
            
            # Pós-processamento
            final_response = await self._post_process_response(response, enriched_context)
            
            logger.info("✅ Mensagem processada com sucesso")
            return final_response
            
        except Exception as e:
            logger.error(f"❌ Erro ao processar mensagem: {{e}}")
            return self._get_error_response(str(e))
    
    async def _process_by_specialization(self, message: str, context: Dict[str, Any]) -> str:
        """Processa mensagem baseado na especialização"""
        {methods}
    
    def _enrich_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Enriquece contexto com dados específicos da especialização"""
        
        enriched = context.copy()
        enriched.update({{
            'agent_name': self.config.name,
            'specialization': self.specialization,
            'tools': self.tools,
            'template': self.template,
            'timestamp': datetime.now().isoformat()
        }})
        
        return enriched
    
    async def _post_process_response(self, response: str, context: Dict[str, Any]) -> str:
        """Pós-processa resposta antes de enviar"""
        
        # Aplica estilo de resposta da especialização
        style = self.template.get('response_style', 'neutral')
        
        if style == 'formal_friendly':
            response = self._apply_formal_friendly_style(response)
        elif style == 'persuasive_friendly':
            response = self._apply_persuasive_style(response)
        elif style == 'efficient_friendly':
            response = self._apply_efficient_style(response)
        elif style == 'technical_helpful':
            response = self._apply_technical_style(response)
        
        return response
    
    def _apply_formal_friendly_style(self, response: str) -> str:
        """Aplica estilo formal e amigável"""
        # Implementar personalização de estilo
        return response
    
    def _apply_persuasive_style(self, response: str) -> str:
        """Aplica estilo persuasivo para vendas"""
        # Implementar personalização de estilo
        return response
    
    def _apply_efficient_style(self, response: str) -> str:
        """Aplica estilo eficiente para agendamentos"""
        # Implementar personalização de estilo
        return response
    
    def _apply_technical_style(self, response: str) -> str:
        """Aplica estilo técnico para suporte"""
        # Implementar personalização de estilo
        return response
    
    def _get_error_response(self, error: str) -> str:
        """Gera resposta amigável para erros"""
        
        error_responses = {{
            "timeout": "Desculpe, demorei um pouco para processar. Pode repetir sua mensagem?",
            "unknown": "Ops! Algo não saiu como esperado. Pode tentar novamente?",
            "validation": "Parece que há algum problema com as informações. Pode verificar e tentar novamente?"
        }}
        
        # Identifica tipo do erro
        if "timeout" in error.lower():
            return error_responses["timeout"]
        elif "validation" in error.lower():
            return error_responses["validation"]
        else:
            return error_responses["unknown"]
'''

        return code
    
    def _to_class_name(self, agent_name: str) -> str:
        """Converte nome do agente para nome de classe Python"""
        
        # Remove caracteres especiais e converte para PascalCase
        words = agent_name.replace('-', '_').replace('_', ' ').split()
        class_name = ''.join(word.capitalize() for word in words)
        
        return f"{class_name}Agent"
    
    def _generate_imports(self, tools: List[str]) -> str:
        """Gera imports baseado nas ferramentas utilizadas"""
        
        base_imports = """
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional
from loguru import logger

from agno import BaseAgent, AgentConfig
from schemas import AgentSpecialization"""

        tool_imports = []
        
        if "whatsapp" in tools:
            tool_imports.append("from services.evolution import EvolutionService")
        
        if "email" in tools:
            tool_imports.append("import smtplib")
            tool_imports.append("from email.mime.text import MIMEText")
            tool_imports.append("from email.mime.multipart import MIMEMultipart")
        
        if "calendar" in tools:
            tool_imports.append("from google.oauth2 import service_account")
            tool_imports.append("from googleapiclient.discovery import build")
        
        if "webhooks" in tools:
            tool_imports.append("import httpx")
        
        if "database" in tools:
            tool_imports.append("import sqlite3")
            tool_imports.append("from contextlib import asynccontextmanager")
        
        all_imports = [base_imports] + tool_imports
        return '\n'.join(all_imports)
    
    def _generate_specialized_methods(self, specialization: AgentSpecialization) -> str:
        """Gera métodos específicos da especialização"""
        
        methods = {
            AgentSpecialization.ATENDIMENTO: '''
        if self._is_escalation_needed(message):
            return await self._handle_escalation(message, context)
        elif self._is_faq_question(message):
            return await self._handle_faq(message, context)
        else:
            return await self._handle_general_support(message, context)
    
    async def _handle_escalation(self, message: str, context: Dict[str, Any]) -> str:
        """Trata escalação para atendimento humano"""
        # TODO: Implementar lógica de escalação
        return "Entendo que precisa falar com um atendente. Vou transferir você agora."
    
    async def _handle_faq(self, message: str, context: Dict[str, Any]) -> str:
        """Responde perguntas frequentes"""
        # TODO: Implementar base de conhecimento
        return "Baseado em nossa FAQ, posso ajudá-lo com isso..."
    
    async def _handle_general_support(self, message: str, context: Dict[str, Any]) -> str:
        """Trata suporte geral"""
        # TODO: Implementar lógica de suporte geral
        return "Vou ajudá-lo com sua questão. Pode me dar mais detalhes?"
    
    def _is_escalation_needed(self, message: str) -> bool:
        """Verifica se precisa escalar para humano"""
        keywords = self.template.get('escalation_keywords', [])
        return any(keyword.lower() in message.lower() for keyword in keywords)
    
    def _is_faq_question(self, message: str) -> bool:
        """Verifica se é pergunta frequente"""
        # TODO: Implementar detecção de FAQ
        return False''',
            
            AgentSpecialization.VENDAS: '''
        # Identifica estágio do funil de vendas
        stage = self._identify_sales_stage(message, context)
        
        if stage == "awareness":
            return await self._handle_awareness(message, context)
        elif stage == "interest":
            return await self._handle_interest(message, context)
        elif stage == "consideration":
            return await self._handle_consideration(message, context)
        elif stage == "intent":
            return await self._handle_intent(message, context)
        else:
            return await self._handle_general_sales(message, context)
    
    def _identify_sales_stage(self, message: str, context: Dict[str, Any]) -> str:
        """Identifica estágio do funil de vendas"""
        # TODO: Implementar lógica de identificação de estágio
        return "interest"
    
    async def _handle_awareness(self, message: str, context: Dict[str, Any]) -> str:
        """Trata fase de conscientização"""
        return "Que bom que você tem interesse! Deixe-me te mostrar como podemos ajudar..."
    
    async def _handle_interest(self, message: str, context: Dict[str, Any]) -> str:
        """Trata fase de interesse"""
        return "Perfeito! Para te ajudar melhor, me conta qual sua principal necessidade..."
    
    async def _handle_consideration(self, message: str, context: Dict[str, Any]) -> str:
        """Trata fase de consideração"""
        return "Vejo que está avaliando opções. Nossa solução se diferencia porque..."
    
    async def _handle_intent(self, message: str, context: Dict[str, Any]) -> str:
        """Trata intenção de compra"""
        return "Ótimo! Vou preparar uma proposta personalizada para você..."
    
    async def _handle_general_sales(self, message: str, context: Dict[str, Any]) -> str:
        """Trata vendas em geral"""
        return "Como posso te ajudar a encontrar a solução ideal?"''',
            
            AgentSpecialization.AGENDAMENTO: '''
        if self._is_booking_request(message):
            return await self._handle_booking(message, context)
        elif self._is_cancellation_request(message):
            return await self._handle_cancellation(message, context)
        elif self._is_reschedule_request(message):
            return await self._handle_reschedule(message, context)
        else:
            return await self._handle_availability_check(message, context)
    
    def _is_booking_request(self, message: str) -> bool:
        """Verifica se é solicitação de agendamento"""
        keywords = ["agendar", "marcar", "reservar", "horário", "consulta"]
        return any(keyword in message.lower() for keyword in keywords)
    
    def _is_cancellation_request(self, message: str) -> bool:
        """Verifica se é solicitação de cancelamento"""
        keywords = ["cancelar", "desmarcar", "não posso ir"]
        return any(keyword in message.lower() for keyword in keywords)
    
    def _is_reschedule_request(self, message: str) -> bool:
        """Verifica se é solicitação de reagendamento"""
        keywords = ["reagendar", "mudar horário", "trocar data"]
        return any(keyword in message.lower() for keyword in keywords)
    
    async def _handle_booking(self, message: str, context: Dict[str, Any]) -> str:
        """Trata agendamento"""
        return "Vou te ajudar a agendar! Qual serviço você precisa e qual sua preferência de horário?"
    
    async def _handle_cancellation(self, message: str, context: Dict[str, Any]) -> str:
        """Trata cancelamento"""
        return "Sem problemas! Para cancelar, preciso do seu nome e horário agendado."
    
    async def _handle_reschedule(self, message: str, context: Dict[str, Any]) -> str:
        """Trata reagendamento"""
        return "Claro! Vou te ajudar a reagendar. Qual seria a nova data de preferência?"
    
    async def _handle_availability_check(self, message: str, context: Dict[str, Any]) -> str:
        """Verifica disponibilidade"""
        return "Deixe-me verificar nossos horários disponíveis..."''',
            
            AgentSpecialization.SUPORTE: '''
        if self._is_urgent_issue(message):
            return await self._handle_urgent_support(message, context)
        elif self._is_common_issue(message):
            return await self._handle_common_issue(message, context)
        else:
            return await self._handle_technical_diagnosis(message, context)
    
    def _is_urgent_issue(self, message: str) -> bool:
        """Verifica se é problema urgente"""
        keywords = ["urgente", "parado", "não funciona", "erro crítico"]
        return any(keyword in message.lower() for keyword in keywords)
    
    def _is_common_issue(self, message: str) -> bool:
        """Verifica se é problema comum"""
        # TODO: Implementar detecção de problemas comuns
        return False
    
    async def _handle_urgent_support(self, message: str, context: Dict[str, Any]) -> str:
        """Trata suporte urgente"""
        return "Entendo que é urgente! Vou priorizar seu atendimento. Pode me dar mais detalhes do problema?"
    
    async def _handle_common_issue(self, message: str, context: Dict[str, Any]) -> str:
        """Trata problemas comuns"""
        return "Esse é um problema que já vi antes. Vamos tentar essa solução..."
    
    async def _handle_technical_diagnosis(self, message: str, context: Dict[str, Any]) -> str:
        """Faz diagnóstico técnico"""
        questions = self.template.get('diagnostic_questions', [])
        if questions:
            return f"Para te ajudar melhor: {questions[0]}"
        return "Vou te ajudar a resolver isso. Pode me dar mais detalhes técnicos?"''',
            
            AgentSpecialization.CUSTOM: '''
        # Processa mensagem com lógica personalizada
        return await self._handle_custom_logic(message, context)
    
    async def _handle_custom_logic(self, message: str, context: Dict[str, Any]) -> str:
        """Implementa lógica personalizada"""
        # TODO: Implementar lógica específica baseada nas instruções customizadas
        return "Processando sua mensagem com lógica personalizada..."'''
        }
        
        return methods.get(specialization, methods[AgentSpecialization.CUSTOM])
    
    def _generate_tool_setup(self, tools: List[str], agent_name: str) -> str:
        """Gera código de configuração das ferramentas"""
        
        setup_code = []
        
        for tool in tools:
            config = self.get_tool_config(AgentTool(tool), agent_name)
            
            if tool == "whatsapp":
                setup_code.append(f'''
        # Configuração WhatsApp
        if "whatsapp" in self.tools:
            self.whatsapp_service = EvolutionService(self.config.settings)
            self.whatsapp_config = {config}
            logger.info("📱 WhatsApp service configurado")''')
            
            elif tool == "email":
                setup_code.append(f'''
        # Configuração E-mail
        if "email" in self.tools:
            self.email_config = {config}
            logger.info("📧 Email service configurado")''')
            
            elif tool == "calendar":
                setup_code.append(f'''
        # Configuração Calendário
        if "calendar" in self.tools:
            self.calendar_config = {config}
            logger.info("📅 Calendar service configurado")''')
            
            elif tool == "webhooks":
                setup_code.append(f'''
        # Configuração Webhooks
        if "webhooks" in self.tools:
            self.webhook_config = {config}
            self.http_client = httpx.AsyncClient()
            logger.info("🔗 Webhook service configurado")''')
            
            elif tool == "database":
                setup_code.append(f'''
        # Configuração Database
        if "database" in self.tools:
            self.db_config = {config}
            self._setup_database()
            logger.info("🗄️ Database service configurado")''')
        
        return '\n'.join(setup_code) if setup_code else '        pass  # Nenhuma ferramenta para configurar'
    
    # UTILITÁRIOS E HELPERS
    
    async def validate_agent_config(self, agent_data: AgentCreate) -> Dict[str, Any]:
        """
        Valida configuração do agente
        
        Args:
            agent_data: Dados do agente
            
        Returns:
            Dict com resultado da validação
        """
        
        issues = []
        warnings = []
        
        # Valida nome
        if not agent_data.agent_name.replace('-', '').replace('_', '').isalnum():
            issues.append("Nome do agente deve conter apenas letras, números, hífen e underscore")
        
        # Valida instruções
        if len(agent_data.instructions) < 50:
            warnings.append("Instruções muito curtas podem resultar em comportamento inconsistente")
        
        if len(agent_data.instructions) > 8000:
            warnings.append("Instruções muito longas podem impactar performance")
        
        # Valida combinação de ferramentas
        if "calendar" in agent_data.tools and agent_data.specialization != AgentSpecialization.AGENDAMENTO:
            warnings.append("Ferramenta Calendar é mais efetiva com especialização Agendamento")
        
        if "database" in agent_data.tools and len(agent_data.tools) == 1:
            warnings.append("Database sozinho pode limitar interatividade do agente")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "score": max(0, 100 - len(issues) * 25 - len(warnings) * 5)
        }
    
    def get_suggested_improvements(self, agent_data: AgentCreate) -> List[str]:
        """
        Sugere melhorias para configuração do agente
        
        Args:
            agent_data: Dados do agente
            
        Returns:
            Lista de sugestões
        """
        
        suggestions = []
        template = self.get_specialization_template(agent_data.specialization)
        
        # Sugestões baseadas na especialização
        suggested_tools = template.get("suggested_tools", [])
        missing_tools = set(suggested_tools) - set(agent_data.tools)
        
        if missing_tools:
            suggestions.append(f"Considere adicionar as ferramentas: {', '.join(missing_tools)}")
        
        # Sugestões baseadas nas instruções
        if "por favor" not in agent_data.instructions.lower():
            suggestions.append("Inclua palavras de cortesia nas instruções para melhor experiência do usuário")
        
        if agent_data.specialization == AgentSpecialization.VENDAS and "objeção" not in agent_data.instructions.lower():
            suggestions.append("Para vendas, considere incluir estratégias para lidar com objeções")
        
        return suggestions
    
    def estimate_performance_metrics(self, agent_data: AgentCreate) -> Dict[str, Any]:
        """
        Estima métricas de performance baseado na configuração
        
        Args:
            agent_data: Dados do agente
            
        Returns:
            Dict com estimativas de performance
        """
        
        base_response_time = 1.5  # segundos
        
        # Ajusta baseado no número de ferramentas
        tool_overhead = len(agent_data.tools) * 0.3
        
        # Ajusta baseado no tamanho das instruções
        instruction_complexity = len(agent_data.instructions) / 1000 * 0.2
        
        estimated_response_time = base_response_time + tool_overhead + instruction_complexity
        
        # Calcula outras métricas
        specialization_multiplier = {
            AgentSpecialization.ATENDIMENTO: 1.0,
            AgentSpecialization.VENDAS: 1.2,
            AgentSpecialization.AGENDAMENTO: 0.8,
            AgentSpecialization.SUPORTE: 1.3,
            AgentSpecialization.CUSTOM: 1.1
        }
        
        complexity_score = min(100, len(agent_data.tools) * 20 + len(agent_data.instructions) / 50)
        
        return {
            "estimated_response_time_seconds": round(estimated_response_time, 2),
            "complexity_score": round(complexity_score, 1),
            "specialization_efficiency": specialization_multiplier.get(agent_data.specialization, 1.0),
            "recommended_concurrent_users": max(1, int(20 / estimated_response_time)),
            "memory_usage_mb": round(50 + len(agent_data.tools) * 10 + len(agent_data.instructions) / 100, 1)
        }