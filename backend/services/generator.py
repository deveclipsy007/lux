"""
Serviço de geração de código para agentes SDK

Este serviço é responsável por gerar todos os arquivos de código Python
necessários para um agente Agno baseado nas especificações fornecidas
pelo usuário através da interface web.

Funcionalidades:
- Geração de arquivos principais (main.py, agent.py)
- Geração de serviços específicos por ferramenta
- Templates personalizáveis por especialização
- Validação de código gerado
- Sistema de versionamento de templates

Autor: Agno SDK Agent Generator
Data: 2025-01-24
"""

import os
import re
import json
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from string import Template
from jinja2 import Environment, BaseLoader, TemplateError

from loguru import logger
try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings

from schemas import AgentCreate, AgentGeneratedFiles, FileData, AgentSpecialization, AgentTool
from services.agno import AgnoService

class TemplateLoader(BaseLoader):
    """Loader personalizado para templates Jinja2"""
    
    def __init__(self, templates: Dict[str, str]):
        self.templates = templates
    
    def get_source(self, environment: Environment, template: str) -> Tuple[str, None, None]:
        if template not in self.templates:
            raise TemplateError(f"Template '{template}' não encontrado")
        
        source = self.templates[template]
        return source, None, None  # source, path, uptodate

class CodeGeneratorService:
    """
    Serviço principal para geração de código de agentes
    """
    
    def __init__(self, settings):
        self.settings = settings
        self.agno_service = AgnoService(settings)
        
        # Configuração do Jinja2
        self.jinja_env = None
        self._setup_jinja()
        
        # Cache de templates
        self._templates_cache: Dict[str, str] = {}
        self._load_templates()
        
        logger.info("🏗️ CodeGeneratorService inicializado")
    
    def _setup_jinja(self):
        """Configura ambiente Jinja2 com extensões e filtros personalizados"""
        
        # Carrega templates
        loader = TemplateLoader(self._get_all_templates())
        
        self.jinja_env = Environment(
            loader=loader,
            autoescape=False,  # Código Python não precisa de escape
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Adiciona filtros personalizados
        self.jinja_env.filters['to_class_name'] = self._to_class_name
        self.jinja_env.filters['to_var_name'] = self._to_var_name
        self.jinja_env.filters['indent'] = self._indent_text
        self.jinja_env.filters['format_docstring'] = self._format_docstring
        self.jinja_env.filters['escape_quotes'] = self._escape_quotes
        
        # Adiciona funções globais
        self.jinja_env.globals['datetime'] = datetime
        self.jinja_env.globals['enumerate'] = enumerate
        self.jinja_env.globals['len'] = len
    
    def _load_templates(self):
        """Carrega todos os templates para o cache"""
        
        templates = self._get_all_templates()
        self._templates_cache.update(templates)
        
        logger.debug(f"📚 {len(templates)} templates carregados")
    
    # GERAÇÃO PRINCIPAL
    
    async def generate_agent_files(self, agent_data: AgentCreate) -> AgentGeneratedFiles:
        """
        Gera todos os arquivos necessários para um agente
        
        Args:
            agent_data: Dados do agente fornecidos pelo usuário
            
        Returns:
            AgentGeneratedFiles com lista de arquivos gerados
        """
        
        logger.info(f"🏗️ Gerando arquivos para agente: {agent_data.agent_name}")
        
        try:
            # Validação inicial
            await self._validate_agent_data(agent_data)
            
            # Prepara contexto para templates
            context = await self._build_template_context(agent_data)
            
            # Gera arquivos principais
            files = []
            
            # 1. main.py - Arquivo principal de execução
            main_content = await self._generate_main_py(context)
            files.append(FileData(path="backend/main.py", content=main_content))
            
            # 2. agent.py - Classe do agente
            agent_content = await self._generate_agent_py(context)
            files.append(FileData(path="backend/agent.py", content=agent_content))
            
            # 3. config.py - Configurações do agente
            config_content = await self._generate_config_py(context)
            files.append(FileData(path="backend/config.py", content=config_content))
            
            # 4. requirements.txt - Dependências
            requirements_content = await self._generate_requirements_txt(context)
            files.append(FileData(path="backend/requirements.txt", content=requirements_content))
            
            # 5. .env.example - Variáveis de ambiente
            env_content = await self._generate_env_example(context)
            files.append(FileData(path="backend/.env.example", content=env_content))
            
            # 6. Serviços específicos por ferramenta
            service_files = await self._generate_service_files(context)
            files.extend(service_files)
            
            # 7. README.md específico do agente
            readme_content = await self._generate_agent_readme(context)
            files.append(FileData(path="backend/README.md", content=readme_content))
            
            # 8. Dockerfile (opcional)
            if self._should_generate_docker(context):
                docker_content = await self._generate_dockerfile(context)
                files.append(FileData(path="backend/Dockerfile", content=docker_content))
            
            logger.info(f"✅ {len(files)} arquivos gerados para {agent_data.agent_name}")
            
            return AgentGeneratedFiles(
                files=files,
                agent_name=agent_data.agent_name,
                specialization=agent_data.specialization,
                tools=agent_data.tools,
                generated_at=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"❌ Erro ao gerar arquivos para {agent_data.agent_name}: {e}")
            raise
    
    async def _validate_agent_data(self, agent_data: AgentCreate):
        """Valida dados do agente antes da geração"""
        
        # Validação via AgnoService
        validation = await self.agno_service.validate_agent_config(agent_data)
        
        if not validation["valid"]:
            error_msg = "; ".join(validation["issues"])
            raise ValueError(f"Configuração inválida: {error_msg}")
        
        # Logs de warnings
        for warning in validation["warnings"]:
            logger.warning(f"⚠️ {warning}")
    
    async def _build_template_context(self, agent_data: AgentCreate) -> Dict[str, Any]:
        """Constrói contexto completo para os templates"""
        
        # Dados básicos do agente
        context = {
            "agent": {
                "name": agent_data.agent_name,
                "class_name": self._to_class_name(agent_data.agent_name),
                "instructions": agent_data.instructions,
                "specialization": agent_data.specialization,
                "tools": agent_data.tools
            },
            "generation": {
                "timestamp": datetime.now(),
                "generator_version": "1.0.0",
                "agno_version": "v1.8.0"
            }
        }
        
        # Enriquece com dados da especialização
        template = self.agno_service.get_specialization_template(agent_data.specialization)
        context["specialization"] = template
        
        # Configurações das ferramentas
        context["tools_config"] = {}
        for tool in agent_data.tools:
            config = self.agno_service.get_tool_config(AgentTool(tool), agent_data.agent_name)
            context["tools_config"][tool] = config
        
        # Instrução completa construída
        context["agent"]["full_instructions"] = self.agno_service.build_agent_instructions(agent_data)
        
        # Métricas estimadas
        context["performance"] = self.agno_service.estimate_performance_metrics(agent_data)
        
        # Sugestões de melhoria
        context["suggestions"] = self.agno_service.get_suggested_improvements(agent_data)
        
        return context
    
    # GERADORES DE ARQUIVOS ESPECÍFICOS
    
    async def _generate_main_py(self, context: Dict[str, Any]) -> str:
        """Gera arquivo main.py principal"""
        
        template = self.jinja_env.get_template("main.py")
        content = template.render(context)
        
        return self._clean_generated_code(content)
    
    async def _generate_agent_py(self, context: Dict[str, Any]) -> str:
        """Gera arquivo da classe do agente"""
        
        template = self.jinja_env.get_template("agent.py")
        content = template.render(context)
        
        return self._clean_generated_code(content)
    
    async def _generate_config_py(self, context: Dict[str, Any]) -> str:
        """Gera arquivo de configurações"""
        
        template = self.jinja_env.get_template("config.py")
        content = template.render(context)
        
        return self._clean_generated_code(content)
    
    async def _generate_requirements_txt(self, context: Dict[str, Any]) -> str:
        """Gera arquivo requirements.txt baseado nas ferramentas"""
        
        base_requirements = [
            "agno>=1.8.0",
            "fastapi>=0.104.0",
            "uvicorn>=0.24.0",
            "pydantic>=2.0.0",
            "loguru>=0.7.0",
            "python-dotenv>=1.0.0",
            "httpx>=0.25.0"
        ]
        
        # Adiciona dependências baseadas nas ferramentas
        tools = context["agent"]["tools"]
        
        if "whatsapp" in tools:
            base_requirements.extend([
                "websockets>=11.0",
                "pillow>=10.0.0"  # Para processamento de imagens
            ])
        
        if "email" in tools:
            base_requirements.extend([
                "aiosmtplib>=3.0.0",
                "email-validator>=2.0.0"
            ])
        
        if "calendar" in tools:
            base_requirements.extend([
                "google-api-python-client>=2.100.0",
                "google-auth>=2.23.0",
                "google-auth-oauthlib>=1.1.0"
            ])
        
        if "database" in tools:
            base_requirements.extend([
                "aiosqlite>=0.19.0",
                "alembic>=1.12.0"  # Para migrações
            ])
        
        if "webhooks" in tools:
            base_requirements.append("pyngrok>=7.0.0")  # Para túneis em desenvolvimento
        
        # Remove duplicatas e ordena
        unique_requirements = sorted(set(base_requirements))
        
        return "\n".join(unique_requirements) + "\n"
    
    async def _generate_env_example(self, context: Dict[str, Any]) -> str:
        """Gera arquivo .env.example"""
        
        template = self.jinja_env.get_template("env.example")
        content = template.render(context)
        
        return content
    
    async def _generate_service_files(self, context: Dict[str, Any]) -> List[FileData]:
        """Gera arquivos de serviços específicos das ferramentas"""
        
        files = []
        tools = context["agent"]["tools"]
        
        if "whatsapp" in tools:
            content = await self._generate_whatsapp_service(context)
            files.append(FileData(path="backend/services/whatsapp_service.py", content=content))
        
        if "email" in tools:
            content = await self._generate_email_service(context)
            files.append(FileData(path="backend/services/email_service.py", content=content))
        
        if "calendar" in tools:
            content = await self._generate_calendar_service(context)
            files.append(FileData(path="backend/services/calendar_service.py", content=content))
        
        if "database" in tools:
            content = await self._generate_database_service(context)
            files.append(FileData(path="backend/services/database_service.py", content=content))
        
        if "webhooks" in tools:
            content = await self._generate_webhook_service(context)
            files.append(FileData(path="backend/services/webhook_service.py", content=content))
        
        # Sempre gera __init__.py para o pacote services
        init_content = self._generate_services_init(tools)
        files.append(FileData(path="backend/services/__init__.py", content=init_content))
        
        return files
    
    async def _generate_whatsapp_service(self, context: Dict[str, Any]) -> str:
        """Gera serviço específico do WhatsApp"""
        
        template = self.jinja_env.get_template("services/whatsapp_service.py")
        content = template.render(context)
        
        return self._clean_generated_code(content)
    
    async def _generate_email_service(self, context: Dict[str, Any]) -> str:
        """Gera serviço de email"""
        
        template = self.jinja_env.get_template("services/email_service.py")
        content = template.render(context)
        
        return self._clean_generated_code(content)
    
    async def _generate_calendar_service(self, context: Dict[str, Any]) -> str:
        """Gera serviço de calendário"""
        
        template = self.jinja_env.get_template("services/calendar_service.py")
        content = template.render(context)
        
        return self._clean_generated_code(content)
    
    async def _generate_database_service(self, context: Dict[str, Any]) -> str:
        """Gera serviço de banco de dados"""
        
        template = self.jinja_env.get_template("services/database_service.py")
        content = template.render(context)
        
        return self._clean_generated_code(content)
    
    async def _generate_webhook_service(self, context: Dict[str, Any]) -> str:
        """Gera serviço de webhooks"""
        
        template = self.jinja_env.get_template("services/webhook_service.py")
        content = template.render(context)
        
        return self._clean_generated_code(content)
    
    def _generate_services_init(self, tools: List[str]) -> str:
        """Gera __init__.py do pacote services"""
        
        imports = []
        
        if "whatsapp" in tools:
            imports.append("from .whatsapp_service import WhatsAppService")
        if "email" in tools:
            imports.append("from .email_service import EmailService")
        if "calendar" in tools:
            imports.append("from .calendar_service import CalendarService")
        if "database" in tools:
            imports.append("from .database_service import DatabaseService")
        if "webhooks" in tools:
            imports.append("from .webhook_service import WebhookService")
        
        all_exports = [cls.split("import ")[-1] for cls in imports]
        
        content = f'''"""
Serviços do agente

Este pacote contém todos os serviços específicos das ferramentas
configuradas para este agente.
"""

{chr(10).join(imports)}

__all__ = {all_exports}
'''
        
        return content
    
    async def _generate_agent_readme(self, context: Dict[str, Any]) -> str:
        """Gera README específico do agente"""
        
        template = self.jinja_env.get_template("README.md")
        content = template.render(context)
        
        return content
    
    async def _generate_dockerfile(self, context: Dict[str, Any]) -> str:
        """Gera Dockerfile para containerização"""
        
        template = self.jinja_env.get_template("Dockerfile")
        content = template.render(context)
        
        return content
    
    def _should_generate_docker(self, context: Dict[str, Any]) -> bool:
        """Determina se deve gerar Dockerfile"""
        
        # Por enquanto, sempre gera para facilitar deployment
        return True
    
    # TEMPLATES JINJA2
    
    def _get_all_templates(self) -> Dict[str, str]:
        """Retorna todos os templates Jinja2"""
        
        return {
            "main.py": self._get_main_template(),
            "agent.py": self._get_agent_template(), 
            "config.py": self._get_config_template(),
            "env.example": self._get_env_template(),
            "services/whatsapp_service.py": self._get_whatsapp_service_template(),
            "services/email_service.py": self._get_email_service_template(),
            "services/calendar_service.py": self._get_calendar_service_template(),
            "services/database_service.py": self._get_database_service_template(),
            "services/webhook_service.py": self._get_webhook_service_template(),
            "README.md": self._get_readme_template(),
            "Dockerfile": self._get_dockerfile_template()
        }
    
    def _get_main_template(self) -> str:
        """Template do arquivo main.py"""
        
        return '''#!/usr/bin/env python3
"""
{{ agent.name | title }} - Agente {{ agent.specialization }}

Agente gerado automaticamente pelo Agno SDK Agent Generator
Especialização: {{ agent.specialization }}
Ferramentas: {{ agent.tools | join(', ') }}

Gerado em: {{ generation.timestamp.strftime('%d/%m/%Y às %H:%M') }}
"""

import asyncio
import os
import sys
from pathlib import Path

# Adiciona o diretório atual ao Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from loguru import logger
from config import AgentConfig
from agent import {{ agent.class_name }}

def setup_logging():
    """Configura sistema de logging"""
    
    # Remove handler padrão
    logger.remove()
    
    # Console handler
    logger.add(
        sys.stderr,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan> - <level>{message}</level>",
        level="INFO"
    )
    
    # Arquivo de log
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logger.add(
        log_dir / "{{ agent.name }}.log",
        rotation="10 MB",
        retention="7 days",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
    )

async def main():
    """Função principal do agente"""
    
    setup_logging()
    
    logger.info("🚀 Iniciando {{ agent.name }}")
    logger.info(f"📋 Especialização: {{ agent.specialization }}")
    logger.info(f"🔧 Ferramentas: {{ agent.tools | join(', ') }}")
    
    try:
        # Carrega configuração
        config = AgentConfig()
        
        # Inicializa agente
        agent = {{ agent.class_name }}(config)
        
        # Inicia execução
        await agent.start()
        
    except KeyboardInterrupt:
        logger.info("👋 Agente interrompido pelo usuário")
    except Exception as e:
        logger.error(f"💥 Erro fatal: {e}")
        sys.exit(1)
    finally:
        logger.info("⏹️ {{ agent.name }} finalizado")

if __name__ == "__main__":
    asyncio.run(main())
'''
    
    def _get_agent_template(self) -> str:
        """Template da classe do agente"""
        
        return '''"""
{{ agent.class_name }} - Implementação do agente {{ agent.specialization }}

Este arquivo contém a implementação principal do agente, incluindo
processamento de mensagens e lógica específica da especialização.
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional

from loguru import logger
from agno import BaseAgent

{% if 'whatsapp' in agent.tools %}
from services.whatsapp_service import WhatsAppService
{% endif %}
{% if 'email' in agent.tools %}
from services.email_service import EmailService
{% endif %}
{% if 'calendar' in agent.tools %}
from services.calendar_service import CalendarService
{% endif %}
{% if 'database' in agent.tools %}
from services.database_service import DatabaseService
{% endif %}
{% if 'webhooks' in agent.tools %}
from services.webhook_service import WebhookService
{% endif %}

class {{ agent.class_name }}(BaseAgent):
    """
    {{ agent.name | title }} - Agente especializado em {{ agent.specialization }}
    
    Ferramentas disponíveis:
    {% for tool in agent.tools %}
    - {{ tool | title }}
    {% endfor %}
    
    Instruções do agente:
    {{ agent.instructions | format_docstring | indent(4) }}
    """
    
    def __init__(self, config):
        super().__init__(config)
        
        # Configurações específicas
        self.agent_name = "{{ agent.name }}"
        self.specialization = "{{ agent.specialization }}"
        self.tools = {{ agent.tools }}
        
        # Serviços
        self.services = {}
        
        # Estatísticas
        self.messages_processed = 0
        self.errors_count = 0
        self.start_time = None
        
        logger.info(f"🤖 {self.agent_name} inicializado")
    
    async def start(self):
        """Inicia o agente e seus serviços"""
        
        self.start_time = datetime.now()
        
        try:
            # Inicializa serviços
            await self._setup_services()
            
            # Loop principal
            logger.info("✅ Agente pronto para receber mensagens")
            await self._main_loop()
            
        except Exception as e:
            logger.error(f"❌ Erro na inicialização: {e}")
            raise
    
    async def _setup_services(self):
        """Configura todos os serviços necessários"""
        
        {% if 'whatsapp' in agent.tools %}
        # WhatsApp Service
        if "whatsapp" in self.tools:
            self.services['whatsapp'] = WhatsAppService(self.config)
            await self.services['whatsapp'].initialize()
            logger.info("📱 WhatsApp service configurado")
        {% endif %}
        
        {% if 'email' in agent.tools %}
        # Email Service
        if "email" in self.tools:
            self.services['email'] = EmailService(self.config)
            await self.services['email'].initialize()
            logger.info("📧 Email service configurado")
        {% endif %}
        
        {% if 'calendar' in agent.tools %}
        # Calendar Service
        if "calendar" in self.tools:
            self.services['calendar'] = CalendarService(self.config)
            await self.services['calendar'].initialize()
            logger.info("📅 Calendar service configurado")
        {% endif %}
        
        {% if 'database' in agent.tools %}
        # Database Service
        if "database" in self.tools:
            self.services['database'] = DatabaseService(self.config)
            await self.services['database'].initialize()
            logger.info("🗄️ Database service configurado")
        {% endif %}
        
        {% if 'webhooks' in agent.tools %}
        # Webhook Service
        if "webhooks" in self.tools:
            self.services['webhooks'] = WebhookService(self.config)
            await self.services['webhooks'].initialize()
            logger.info("🔗 Webhook service configurado")
        {% endif %}
    
    async def _main_loop(self):
        """Loop principal do agente"""
        
        while True:
            try:
                # Verifica mensagens pendentes em todos os serviços
                await self._check_for_messages()
                
                # Pausa para não consumir CPU desnecessariamente
                await asyncio.sleep(1)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"❌ Erro no loop principal: {e}")
                self.errors_count += 1
                await asyncio.sleep(5)  # Pausa em caso de erro
    
    async def _check_for_messages(self):
        """Verifica mensagens pendentes em todos os serviços"""
        
        {% if 'whatsapp' in agent.tools %}
        # Verifica mensagens do WhatsApp
        if 'whatsapp' in self.services:
            messages = await self.services['whatsapp'].get_pending_messages()
            for message in messages:
                await self.process_message(message['content'], message.get('context', {}))
        {% endif %}
        
        # TODO: Implementar verificação para outros serviços
    
    async def process_message(self, message: str, context: Dict[str, Any] = None) -> str:
        """
        Processa uma mensagem recebida
        
        Args:
            message: Texto da mensagem
            context: Contexto adicional (remetente, canal, etc.)
            
        Returns:
            Resposta do agente
        """
        
        try:
            self.messages_processed += 1
            logger.debug(f"📨 Processando mensagem: {message[:50]}...")
            
            # Enriquece contexto
            enriched_context = self._enrich_context(context or {})
            
            # Processa baseado na especialização
            response = await self._process_by_specialization(message, enriched_context)
            
            # Pós-processamento
            final_response = await self._post_process_response(response, enriched_context)
            
            logger.info("✅ Mensagem processada com sucesso")
            return final_response
            
        except Exception as e:
            logger.error(f"❌ Erro ao processar mensagem: {e}")
            self.errors_count += 1
            return self._get_error_response(str(e))
    
    async def _process_by_specialization(self, message: str, context: Dict[str, Any]) -> str:
        """Processa mensagem baseado na especialização"""
        
        {% if agent.specialization == 'Atendimento' %}
        # Lógica específica para Atendimento
        if self._is_greeting(message):
            return self._get_greeting_response()
        elif self._is_help_request(message):
            return await self._handle_help_request(message, context)
        elif self._is_complaint(message):
            return await self._handle_complaint(message, context)
        else:
            return await self._handle_general_inquiry(message, context)
        
        {% elif agent.specialization == 'Vendas' %}
        # Lógica específica para Vendas
        sales_stage = self._identify_sales_stage(message, context)
        
        if sales_stage == "interest":
            return await self._handle_interest_phase(message, context)
        elif sales_stage == "consideration":
            return await self._handle_consideration_phase(message, context)
        elif sales_stage == "decision":
            return await self._handle_decision_phase(message, context)
        else:
            return await self._handle_prospecting(message, context)
        
        {% elif agent.specialization == 'Agendamento' %}
        # Lógica específica para Agendamento
        if self._is_booking_request(message):
            return await self._handle_booking_request(message, context)
        elif self._is_cancellation_request(message):
            return await self._handle_cancellation(message, context)
        elif self._is_reschedule_request(message):
            return await self._handle_reschedule(message, context)
        else:
            return await self._handle_availability_inquiry(message, context)
        
        {% elif agent.specialization == 'Suporte' %}
        # Lógica específica para Suporte
        if self._is_urgent_issue(message):
            return await self._handle_urgent_support(message, context)
        elif self._is_known_issue(message):
            return await self._handle_known_issue(message, context)
        else:
            return await self._handle_technical_support(message, context)
        
        {% else %}
        # Lógica personalizada
        return await self._handle_custom_logic(message, context)
        {% endif %}
    
    # Métodos específicos da especialização
    {% if agent.specialization == 'Atendimento' %}
    
    def _is_greeting(self, message: str) -> bool:
        """Verifica se é uma saudação"""
        greetings = ['oi', 'olá', 'bom dia', 'boa tarde', 'boa noite', 'hello', 'hi']
        return any(greeting in message.lower() for greeting in greetings)
    
    def _get_greeting_response(self) -> str:
        """Retorna resposta de saudação"""
        return "Olá! Seja bem-vindo! Como posso ajudá-lo hoje? 😊"
    
    def _is_help_request(self, message: str) -> bool:
        """Verifica se é pedido de ajuda"""
        help_keywords = ['ajuda', 'help', 'socorro', 'auxílio', 'suporte']
        return any(keyword in message.lower() for keyword in help_keywords)
    
    async def _handle_help_request(self, message: str, context: Dict[str, Any]) -> str:
        """Trata pedidos de ajuda"""
        return "Claro! Estou aqui para ajudá-lo. Pode me contar qual é sua dúvida ou necessidade?"
    
    def _is_complaint(self, message: str) -> bool:
        """Verifica se é uma reclamação"""
        complaint_keywords = ['problema', 'reclamação', 'insatisfeito', 'ruim', 'péssimo']
        return any(keyword in message.lower() for keyword in complaint_keywords)
    
    async def _handle_complaint(self, message: str, context: Dict[str, Any]) -> str:
        """Trata reclamações"""
        return "Lamento muito pelo inconveniente! Vou fazer o possível para resolver sua situação. Pode me dar mais detalhes sobre o problema?"
    
    async def _handle_general_inquiry(self, message: str, context: Dict[str, Any]) -> str:
        """Trata consultas gerais"""
        return "Entendi sua mensagem. Deixe-me ajudá-lo da melhor forma possível. Precisa de alguma informação específica?"
    
    {% elif agent.specialization == 'Agendamento' %}
    
    def _is_booking_request(self, message: str) -> bool:
        """Verifica se é solicitação de agendamento"""
        booking_keywords = ['agendar', 'marcar', 'reservar', 'horário', 'consulta']
        return any(keyword in message.lower() for keyword in booking_keywords)
    
    async def _handle_booking_request(self, message: str, context: Dict[str, Any]) -> str:
        """Trata solicitações de agendamento"""
        return "Perfeito! Vou ajudá-lo a agendar. Qual serviço você precisa e qual sua preferência de data e horário?"
    
    # Adicione mais métodos conforme necessário...
    {% endif %}
    
    def _enrich_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Enriquece contexto com informações do agente"""
        
        enriched = context.copy()
        enriched.update({
            'agent_name': self.agent_name,
            'specialization': self.specialization,
            'timestamp': datetime.now().isoformat(),
            'messages_processed': self.messages_processed
        })
        
        return enriched
    
    async def _post_process_response(self, response: str, context: Dict[str, Any]) -> str:
        """Pós-processa resposta antes de enviar"""
        
        # Aplica personalização baseada no contexto
        # TODO: Implementar lógica de personalização
        
        return response
    
    def _get_error_response(self, error: str) -> str:
        """Gera resposta amigável para erros"""
        
        return "Ops! Algo não saiu como esperado. Pode tentar novamente? Se o problema persistir, vou encaminhar para um atendente humano."
    
    async def shutdown(self):
        """Finaliza o agente e seus serviços"""
        
        logger.info("⏹️ Finalizando agente...")
        
        # Finaliza serviços
        for service_name, service in self.services.items():
            try:
                await service.shutdown()
                logger.debug(f"✅ {service_name} service finalizado")
            except Exception as e:
                logger.error(f"❌ Erro ao finalizar {service_name}: {e}")
        
        # Log final de estatísticas
        if self.start_time:
            uptime = datetime.now() - self.start_time
            logger.info(f"📊 Estatísticas finais:")
            logger.info(f"  - Mensagens processadas: {self.messages_processed}")
            logger.info(f"  - Erros ocorridos: {self.errors_count}")
            logger.info(f"  - Tempo de execução: {uptime}")
        
        logger.info("👋 {{ agent.name }} finalizado")
'''
    
    def _get_config_template(self) -> str:
        """Template do arquivo de configuração"""
        
        return '''"""
Configurações do Agente {{ agent.name | title }}

Este arquivo contém todas as configurações necessárias para o funcionamento
do agente, incluindo credenciais de APIs e parâmetros de comportamento.
"""

import os
from typing import Dict, Any, List, Optional
from pathlib import Path

from pydantic import validator
from loguru import logger

class AgentConfig(BaseSettings):
    """
    Configurações do agente {{ agent.name }}
    
    Todas as configurações podem ser definidas via variáveis de ambiente
    ou arquivo .env na raiz do projeto.
    """
    
    # Informações básicas do agente
    agent_name: str = "{{ agent.name }}"
    agent_version: str = "1.0.0"
    specialization: str = "{{ agent.specialization }}"
    tools: List[str] = {{ agent.tools }}
    
    # Configurações de logging
    log_level: str = "INFO"
    log_to_file: bool = True
    
    {% if 'whatsapp' in agent.tools %}
    # Configurações WhatsApp (Evolution API)
    evolution_base_url: str = "https://api.evolution-api.com"
    evolution_api_key: str = ""
    evolution_instance_name: str = "{{ agent.name }}-whatsapp"
    whatsapp_webhook_url: Optional[str] = None
    {% endif %}
    
    {% if 'email' in agent.tools %}
    # Configurações de Email
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    email_from: str = ""
    email_from_name: str = "{{ agent.name | title }}"
    {% endif %}
    
    {% if 'calendar' in agent.tools %}
    # Configurações do Google Calendar
    google_credentials_file: str = "credentials.json"
    google_calendar_id: str = "primary"
    calendar_timezone: str = "America/Sao_Paulo"
    {% endif %}
    
    {% if 'database' in agent.tools %}
    # Configurações do Banco de Dados
    database_url: str = "sqlite:///{{ agent.name }}.db"
    database_echo: bool = False
    {% endif %}
    
    {% if 'webhooks' in agent.tools %}
    # Configurações de Webhooks
    webhook_port: int = 8080
    webhook_host: str = "0.0.0.0"
    webhook_base_path: str = "/webhooks"
    {% endif %}
    
    # Configurações de performance
    max_concurrent_messages: int = {{ performance.recommended_concurrent_users }}
    message_timeout_seconds: int = 30
    retry_attempts: int = 3
    
    # Configurações de comportamento
    default_response_delay_seconds: float = 1.0
    typing_indicator_enabled: bool = True
    read_receipts_enabled: bool = True
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    {% if 'evolution' in agent.tools %}
    @validator('evolution_api_key')
    def validate_evolution_api_key(cls, v):
        if not v:
            logger.warning("⚠️ Evolution API key não configurada")
        return v
    {% endif %}
    
    {% if 'email' in agent.tools %}
    @validator('smtp_password')
    def validate_smtp_password(cls, v):
        if not v:
            logger.warning("⚠️ Credenciais de email não configuradas")
        return v
    {% endif %}
    
    def get_tool_config(self, tool_name: str) -> Dict[str, Any]:
        """
        Obtém configuração específica de uma ferramenta
        
        Args:
            tool_name: Nome da ferramenta
            
        Returns:
            Dict com configurações da ferramenta
        """
        
        configs = {
            {% if 'whatsapp' in agent.tools %}
            'whatsapp': {
                'base_url': self.evolution_base_url,
                'api_key': self.evolution_api_key,
                'instance_name': self.evolution_instance_name,
                'webhook_url': self.whatsapp_webhook_url
            },
            {% endif %}
            {% if 'email' in agent.tools %}
            'email': {
                'smtp_host': self.smtp_host,
                'smtp_port': self.smtp_port,
                'username': self.smtp_username,
                'password': self.smtp_password,
                'from_email': self.email_from,
                'from_name': self.email_from_name
            },
            {% endif %}
            # Adicione configurações para outras ferramentas aqui
        }
        
        return configs.get(tool_name, {})
    
    def validate_required_configs(self) -> List[str]:
        """
        Valida se todas as configurações necessárias estão presentes
        
        Returns:
            Lista de configurações faltantes
        """
        
        missing = []
        
        {% if 'whatsapp' in agent.tools %}
        if not self.evolution_api_key:
            missing.append("EVOLUTION_API_KEY")
        {% endif %}
        
        {% if 'email' in agent.tools %}
        if not self.smtp_password:
            missing.append("SMTP_PASSWORD")
        if not self.email_from:
            missing.append("EMAIL_FROM")
        {% endif %}
        
        return missing
    
    def __post_init__(self):
        """Validação pós-inicialização"""
        
        missing_configs = self.validate_required_configs()
        
        if missing_configs:
            logger.warning(f"⚠️ Configurações faltantes: {', '.join(missing_configs)}")
            logger.info("💡 Verifique o arquivo .env ou variáveis de ambiente")
'''
    
    def _get_env_template(self) -> str:
        """Template do arquivo .env.example"""
        
        return '''# Configurações do Agente {{ agent.name | title }}
# Copie este arquivo para .env e preencha os valores

# Informações básicas
AGENT_NAME="{{ agent.name }}"
LOG_LEVEL=INFO

{% if 'whatsapp' in agent.tools %}
# Evolution API (WhatsApp)
EVOLUTION_BASE_URL=https://api.evolution-api.com
EVOLUTION_API_KEY=your_evolution_api_key_here
EVOLUTION_INSTANCE_NAME={{ agent.name }}-whatsapp
WHATSAPP_WEBHOOK_URL=
{% endif %}

{% if 'email' in agent.tools %}
# Configurações de Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
EMAIL_FROM=your_email@gmail.com
EMAIL_FROM_NAME={{ agent.name | title }}
{% endif %}

{% if 'calendar' in agent.tools %}
# Google Calendar
GOOGLE_CREDENTIALS_FILE=credentials.json
GOOGLE_CALENDAR_ID=primary
CALENDAR_TIMEZONE=America/Sao_Paulo
{% endif %}

{% if 'database' in agent.tools %}
# Banco de Dados
DATABASE_URL=sqlite:///{{ agent.name }}.db
DATABASE_ECHO=false
{% endif %}

{% if 'webhooks' in agent.tools %}
# Webhooks
WEBHOOK_PORT=8080
WEBHOOK_HOST=0.0.0.0
WEBHOOK_BASE_PATH=/webhooks
{% endif %}

# Performance
MAX_CONCURRENT_MESSAGES={{ performance.recommended_concurrent_users }}
MESSAGE_TIMEOUT_SECONDS=30
DEFAULT_RESPONSE_DELAY_SECONDS=1.0
'''
    
    def _get_whatsapp_service_template(self) -> str:
        """Template do serviço WhatsApp"""
        
        return '''"""
Serviço WhatsApp para o agente {{ agent.name }}

Integração com Evolution API para envio e recebimento de mensagens WhatsApp.
"""

import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional

from loguru import logger
import httpx

class WhatsAppService:
    """Serviço de integração com WhatsApp via Evolution API"""
    
    def __init__(self, config):
        self.config = config
        self.tool_config = config.get_tool_config('whatsapp')
        
        self.base_url = self.tool_config['base_url'].rstrip('/')
        self.api_key = self.tool_config['api_key']
        self.instance_name = self.tool_config['instance_name']
        
        self.client = None
        self.pending_messages = []
        
    async def initialize(self):
        """Inicializa o serviço WhatsApp"""
        
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            timeout=30.0
        )
        
        # Testa conexão
        await self._test_connection()
        
        # Configura instância
        await self._setup_instance()
        
        logger.info("📱 WhatsApp service inicializado")
    
    async def _test_connection(self):
        """Testa conexão com Evolution API"""
        
        try:
            response = await self.client.get("/instance/fetchInstances")
            response.raise_for_status()
            logger.debug("✅ Conexão com Evolution API OK")
        except Exception as e:
            logger.error(f"❌ Falha na conexão com Evolution API: {e}")
            raise
    
    async def _setup_instance(self):
        """Configura instância WhatsApp"""
        
        try:
            # Cria ou recupera instância
            response = await self.client.post("/instance/create", json={
                "instanceName": self.instance_name,
                "integration": "WHATSAPP-BAILEYS"
            })
            
            if response.status_code in [200, 201]:
                logger.info(f"✅ Instância {self.instance_name} configurada")
            else:
                logger.warning(f"⚠️ Resposta inesperada ao criar instância: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Erro ao configurar instância: {e}")
            raise
    
    async def send_message(self, to: str, message: str) -> bool:
        """
        Envia mensagem WhatsApp
        
        Args:
            to: Número do destinatário
            message: Texto da mensagem
            
        Returns:
            True se enviada com sucesso
        """
        
        try:
            response = await self.client.post(
                f"/message/sendText/{self.instance_name}",
                json={
                    "number": to,
                    "text": message
                }
            )
            
            if response.is_success:
                logger.info(f"📤 Mensagem enviada para {to}")
                return True
            else:
                logger.error(f"❌ Erro ao enviar mensagem: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro ao enviar mensagem: {e}")
            return False
    
    async def get_pending_messages(self) -> List[Dict[str, Any]]:
        """
        Obtém mensagens pendentes para processamento
        
        Returns:
            Lista de mensagens pendentes
        """
        
        # Por enquanto retorna mensagens do buffer local
        # Em uma implementação completa, integraria com webhooks
        
        messages = self.pending_messages.copy()
        self.pending_messages.clear()
        
        return messages
    
    def add_received_message(self, message_data: Dict[str, Any]):
        """Adiciona mensagem recebida ao buffer de processamento"""
        
        self.pending_messages.append({
            'content': message_data.get('content', ''),
            'from': message_data.get('from', ''),
            'timestamp': datetime.now(),
            'context': message_data
        })
    
    async def get_connection_status(self) -> str:
        """
        Obtém status da conexão WhatsApp
        
        Returns:
            Status da conexão
        """
        
        try:
            response = await self.client.get(f"/instance/connectionState/{self.instance_name}")
            
            if response.is_success:
                data = response.json()
                return data.get('state', 'unknown')
            else:
                return 'error'
                
        except Exception as e:
            logger.error(f"❌ Erro ao verificar status: {e}")
            return 'error'
    
    async def shutdown(self):
        """Finaliza o serviço"""
        
        if self.client:
            await self.client.aclose()
        
        logger.info("📱 WhatsApp service finalizado")
'''
    
    def _get_email_service_template(self) -> str:
        """Template do serviço de email"""
        
        return '''"""
Serviço de Email para o agente {{ agent.name }}

Envio de emails automáticos e notificações.
"""

import asyncio
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional

from loguru import logger

class EmailService:
    """Serviço de email SMTP"""
    
    def __init__(self, config):
        self.config = config
        self.tool_config = config.get_tool_config('email')
        
        self.smtp_host = self.tool_config['smtp_host']
        self.smtp_port = self.tool_config['smtp_port']
        self.username = self.tool_config['username']
        self.password = self.tool_config['password']
        self.from_email = self.tool_config['from_email']
        self.from_name = self.tool_config['from_name']
        
    async def initialize(self):
        """Inicializa o serviço de email"""
        
        # Testa conexão SMTP
        await self._test_connection()
        
        logger.info("📧 Email service inicializado")
    
    async def _test_connection(self):
        """Testa conexão SMTP"""
        
        try:
            server = smtplib.SMTP(self.smtp_host, self.smtp_port)
            server.starttls()
            server.login(self.username, self.password)
            server.quit()
            
            logger.debug("✅ Conexão SMTP OK")
            
        except Exception as e:
            logger.error(f"❌ Falha na conexão SMTP: {e}")
            raise
    
    async def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None
    ) -> bool:
        """
        Envia email
        
        Args:
            to: Destinatário
            subject: Assunto
            body: Corpo do email (texto)
            html_body: Corpo em HTML (opcional)
            
        Returns:
            True se enviado com sucesso
        """
        
        try:
            # Cria mensagem
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to
            msg['Subject'] = subject
            
            # Adiciona corpo em texto
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            # Adiciona corpo em HTML se fornecido
            if html_body:
                msg.attach(MIMEText(html_body, 'html', 'utf-8'))
            
            # Envia email
            server = smtplib.SMTP(self.smtp_host, self.smtp_port)
            server.starttls()
            server.login(self.username, self.password)
            server.send_message(msg)
            server.quit()
            
            logger.info(f"📧 Email enviado para {to}: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao enviar email: {e}")
            return False
    
    async def shutdown(self):
        """Finaliza o serviço"""
        logger.info("📧 Email service finalizado")
'''
    
    def _get_calendar_service_template(self) -> str:
        """Template do serviço de calendário"""
        
        return '''"""
Serviço de Calendário para o agente {{ agent.name }}

Integração com Google Calendar para agendamentos.
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from loguru import logger

# Placeholder - implementação completa requer google-api-python-client
class CalendarService:
    """Serviço de integração com Google Calendar"""
    
    def __init__(self, config):
        self.config = config
        self.tool_config = config.get_tool_config('calendar')
    
    async def initialize(self):
        """Inicializa o serviço de calendário"""
        
        # TODO: Implementar autenticação OAuth com Google
        logger.info("📅 Calendar service inicializado (placeholder)")
    
    async def create_event(self, title: str, start_time: datetime, duration_minutes: int = 60) -> bool:
        """
        Cria evento no calendário
        
        Args:
            title: Título do evento
            start_time: Horário de início
            duration_minutes: Duração em minutos
            
        Returns:
            True se criado com sucesso
        """
        
        # TODO: Implementar criação de evento via Google Calendar API
        logger.info(f"📅 Evento criado: {title} em {start_time}")
        return True
    
    async def shutdown(self):
        """Finaliza o serviço"""
        logger.info("📅 Calendar service finalizado")
'''
    
    def _get_database_service_template(self) -> str:
        """Template do serviço de banco de dados"""
        
        return '''"""
Serviço de Banco de Dados para o agente {{ agent.name }}

Armazenamento de conversas e dados do agente.
"""

import asyncio
import aiosqlite
from datetime import datetime
from typing import List, Dict, Any, Optional

from loguru import logger

class DatabaseService:
    """Serviço de banco de dados SQLite"""
    
    def __init__(self, config):
        self.config = config
        self.tool_config = config.get_tool_config('database')
        self.db_path = "{{ agent.name }}.db"
        
    async def initialize(self):
        """Inicializa o banco de dados"""
        
        # Cria tabelas necessárias
        await self._create_tables()
        
        logger.info("🗄️ Database service inicializado")
    
    async def _create_tables(self):
        """Cria tabelas do banco de dados"""
        
        async with aiosqlite.connect(self.db_path) as db:
            # Tabela de conversas
            await db.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    contact TEXT NOT NULL,
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_message_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'active'
                )
            """)
            
            # Tabela de mensagens
            await db.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id INTEGER,
                    content TEXT NOT NULL,
                    sender TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (conversation_id) REFERENCES conversations (id)
                )
            """)
            
            await db.commit()
    
    async def save_message(self, contact: str, content: str, sender: str) -> int:
        """
        Salva mensagem no banco
        
        Args:
            contact: Contato da conversa
            content: Conteúdo da mensagem
            sender: Remetente (user/agent)
            
        Returns:
            ID da mensagem salva
        """
        
        async with aiosqlite.connect(self.db_path) as db:
            # Busca ou cria conversa
            cursor = await db.execute(
                "SELECT id FROM conversations WHERE contact = ? AND status = 'active'",
                (contact,)
            )
            row = await cursor.fetchone()
            
            if row:
                conversation_id = row[0]
                # Atualiza última mensagem
                await db.execute(
                    "UPDATE conversations SET last_message_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (conversation_id,)
                )
            else:
                # Cria nova conversa
                cursor = await db.execute(
                    "INSERT INTO conversations (contact) VALUES (?)",
                    (contact,)
                )
                conversation_id = cursor.lastrowid
            
            # Salva mensagem
            cursor = await db.execute(
                "INSERT INTO messages (conversation_id, content, sender) VALUES (?, ?, ?)",
                (conversation_id, content, sender)
            )
            
            message_id = cursor.lastrowid
            await db.commit()
            
            return message_id
    
    async def get_conversation_history(self, contact: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Obtém histórico de conversa
        
        Args:
            contact: Contato da conversa
            limit: Limite de mensagens
            
        Returns:
            Lista de mensagens
        """
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT m.content, m.sender, m.timestamp
                FROM messages m
                JOIN conversations c ON m.conversation_id = c.id
                WHERE c.contact = ?
                ORDER BY m.timestamp DESC
                LIMIT ?
            """, (contact, limit))
            
            rows = await cursor.fetchall()
            
            messages = []
            for row in rows:
                messages.append({
                    'content': row[0],
                    'sender': row[1],
                    'timestamp': row[2]
                })
            
            return list(reversed(messages))  # Ordem cronológica
    
    async def shutdown(self):
        """Finaliza o serviço"""
        logger.info("🗄️ Database service finalizado")
'''
    
    def _get_webhook_service_template(self) -> str:
        """Template do serviço de webhooks"""
        
        return '''"""
Serviço de Webhooks para o agente {{ agent.name }}

Recebimento de webhooks de APIs externas.
"""

import asyncio
from typing import Dict, Any, Callable

from loguru import logger

class WebhookService:
    """Serviço de webhooks HTTP"""
    
    def __init__(self, config):
        self.config = config
        self.tool_config = config.get_tool_config('webhooks')
        
        self.webhook_handlers = {}
        
    async def initialize(self):
        """Inicializa o serviço de webhooks"""
        
        # TODO: Implementar servidor HTTP para receber webhooks
        logger.info("🔗 Webhook service inicializado (placeholder)")
    
    def register_handler(self, path: str, handler: Callable):
        """
        Registra handler para um webhook
        
        Args:
            path: Caminho do webhook
            handler: Função para processar o webhook
        """
        
        self.webhook_handlers[path] = handler
        logger.debug(f"🔗 Handler registrado para {path}")
    
    async def shutdown(self):
        """Finaliza o serviço"""
        logger.info("🔗 Webhook service finalizado")
'''
    
    def _get_readme_template(self) -> str:
        """Template do README do agente"""
        
        return '''# {{ agent.name | title }} - Agente {{ agent.specialization }}

> Agente inteligente gerado automaticamente pelo **Agno SDK Agent Generator**

## 📋 Informações Gerais

- **Nome**: {{ agent.name }}
- **Especialização**: {{ agent.specialization }}
- **Ferramentas**: {{ agent.tools | join(', ') }}
- **Gerado em**: {{ generation.timestamp.strftime('%d/%m/%Y às %H:%M') }}

## 🤖 Descrição

{{ agent.instructions | truncate(200) }}...

## 🛠️ Ferramentas Configuradas

{% for tool in agent.tools %}
### {{ tool | title }}

{% if tool == 'whatsapp' %}
- Envio e recebimento de mensagens WhatsApp
- Integração com Evolution API
- Suporte a mídias (imagens, documentos, áudio)
{% elif tool == 'email' %}
- Envio de emails automáticos
- Notificações por email
- Templates personalizáveis
{% elif tool == 'calendar' %}
- Agendamento de compromissos
- Integração com Google Calendar
- Lembretes automáticos
{% elif tool == 'database' %}
- Armazenamento de conversas
- Histórico de mensagens
- Dados de usuários
{% elif tool == 'webhooks' %}
- Recebimento de webhooks
- Integração com APIs externas
- Processamento de eventos
{% endif %}

{% endfor %}

## 🚀 Como Executar

### 1. Instalação

```bash
# Clone ou extraia o projeto
cd {{ agent.name }}

# Crie ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Instale dependências
pip install -r requirements.txt
```

### 2. Configuração

```bash
# Copie o arquivo de exemplo
cp .env.example .env

# Edite o arquivo .env com suas credenciais
nano .env
```

### 3. Execução

```bash
# Execute o agente
python main.py
```

## ⚙️ Configurações Necessárias

{% if 'whatsapp' in agent.tools %}
### WhatsApp (Evolution API)

- `EVOLUTION_BASE_URL`: URL da Evolution API
- `EVOLUTION_API_KEY`: Chave de API da Evolution
- `EVOLUTION_INSTANCE_NAME`: Nome da instância WhatsApp
{% endif %}

{% if 'email' in agent.tools %}
### Email SMTP

- `SMTP_HOST`: Servidor SMTP
- `SMTP_PORT`: Porta SMTP (padrão: 587)
- `SMTP_USERNAME`: Usuário SMTP
- `SMTP_PASSWORD`: Senha SMTP
- `EMAIL_FROM`: Email remetente
{% endif %}

{% if 'calendar' in agent.tools %}
### Google Calendar

- `GOOGLE_CREDENTIALS_FILE`: Arquivo de credenciais OAuth
- `GOOGLE_CALENDAR_ID`: ID do calendário
{% endif %}

Veja o arquivo `.env.example` para a lista completa.

## 📊 Performance Estimada

- **Tempo de resposta**: ~{{ performance.estimated_response_time_seconds }}s
- **Usuários simultâneos**: até {{ performance.recommended_concurrent_users }}
- **Uso de memória**: ~{{ performance.memory_usage_mb }}MB
- **Score de complexidade**: {{ performance.complexity_score }}/100

## 🏗️ Arquitetura

```
{{ agent.name }}/
├── main.py              # Arquivo principal
├── agent.py             # Classe do agente
├── config.py            # Configurações
├── services/            # Serviços das ferramentas
{% for tool in agent.tools %}
│   ├── {{ tool }}_service.py
{% endfor %}
├── logs/                # Arquivos de log
├── requirements.txt     # Dependências
└── .env                 # Variáveis de ambiente
```

## 📝 Logs

O agente gera logs detalhados em:

- **Console**: Informações importantes e erros
- **Arquivo**: `logs/{{ agent.name }}.log` (histórico completo)

Níveis de log disponíveis: `DEBUG`, `INFO`, `WARNING`, `ERROR`

## 🔧 Personalização

Para personalizar o comportamento do agente:

1. **Instruções**: Edite o prompt em `config.py`
2. **Especialização**: Modifique métodos específicos em `agent.py`
3. **Integrações**: Configure serviços individuais em `services/`

## 🆘 Suporte

Se encontrar problemas:

1. Verifique os logs em `logs/{{ agent.name }}.log`
2. Confirme se todas as variáveis do `.env` estão configuradas
3. Teste conexões individuais com cada serviço

---

**Gerado por**: [Agno SDK Agent Generator](https://github.com/agno/agent-generator)  
**Versão**: {{ generation.generator_version }}  
**Framework**: Agno {{ generation.agno_version }}
'''
    
    def _get_dockerfile_template(self) -> str:
        """Template do Dockerfile"""
        
        return '''FROM python:3.11-slim

LABEL maintainer="Agno SDK Agent Generator"
LABEL agent.name="{{ agent.name }}"
LABEL agent.specialization="{{ agent.specialization }}"
LABEL agent.version="1.0.0"

# Variáveis de ambiente
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Diretório de trabalho
WORKDIR /app

# Instala dependências do sistema
RUN apt-get update && apt-get install -y \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

# Copia requirements primeiro (para cache do Docker)
COPY requirements.txt .

# Instala dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia código da aplicação
COPY . .

# Cria diretório de logs
RUN mkdir -p logs

# Expõe porta (se necessário para webhooks)
{% if 'webhooks' in agent.tools %}
EXPOSE 8080
{% endif %}

# Comando padrão
CMD ["python", "main.py"]
'''
    
    # UTILITÁRIOS E FILTROS JINJA2
    
    def _to_class_name(self, name: str) -> str:
        """Converte string para nome de classe Python"""
        # Remove caracteres especiais e converte para PascalCase
        words = re.sub(r'[^a-zA-Z0-9]', ' ', name).split()
        class_name = ''.join(word.capitalize() for word in words if word)
        return f"{class_name}Agent" if not class_name.endswith('Agent') else class_name
    
    def _to_var_name(self, name: str) -> str:
        """Converte string para nome de variável Python"""
        # Remove caracteres especiais e converte para snake_case
        var_name = re.sub(r'[^a-zA-Z0-9]', '_', name.lower())
        var_name = re.sub(r'_+', '_', var_name)
        return var_name.strip('_')
    
    def _indent_text(self, text: str, width: int = 4) -> str:
        """Indenta texto com espaços"""
        lines = text.split('\n')
        indent = ' ' * width
        return '\n'.join(indent + line if line.strip() else line for line in lines)
    
    def _format_docstring(self, text: str) -> str:
        """Formata texto para docstring Python"""
        # Remove quebras de linha excessivas e ajusta espaçamento
        lines = [line.strip() for line in text.split('\n')]
        formatted_lines = []
        
        for line in lines:
            if line:
                formatted_lines.append(line)
            elif formatted_lines and formatted_lines[-1]:
                formatted_lines.append('')
        
        return '\n'.join(formatted_lines)
    
    def _escape_quotes(self, text: str) -> str:
        """Escapa aspas para strings Python"""
        return text.replace('"', '\\"').replace("'", "\\'")
    
    def _clean_generated_code(self, code: str) -> str:
        """Limpa código gerado removendo espaços desnecessários"""
        
        lines = code.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Remove espaços em branco no final da linha
            cleaned_line = line.rstrip()
            cleaned_lines.append(cleaned_line)
        
        # Remove linhas vazias excessivas (mais de 2 consecutivas)
        final_lines = []
        empty_count = 0
        
        for line in cleaned_lines:
            if line.strip():
                final_lines.append(line)
                empty_count = 0
            else:
                empty_count += 1
                if empty_count <= 2:
                    final_lines.append(line)
        
        # Remove linhas vazias do início e fim
        while final_lines and not final_lines[0].strip():
            final_lines.pop(0)
        
        while final_lines and not final_lines[-1].strip():
            final_lines.pop()
        
        return '\n'.join(final_lines) + '\n'