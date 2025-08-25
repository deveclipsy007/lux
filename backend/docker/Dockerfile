# Dockerfile para Evolution API
# Imagem otimizada para produção com multi-stage build
# Autor: AgnoMaster - Evolution API Expert
# Data: 2025-01-24

# Stage 1: Build
FROM python:3.11-slim as builder

# Definir variáveis de ambiente
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Criar diretório de trabalho
WORKDIR /app

# Copiar arquivos de dependências
COPY requirements.txt .
COPY requirements-dev.txt .

# Instalar dependências Python
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim as runtime

# Definir variáveis de ambiente
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.local/bin:$PATH" \
    PYTHONPATH="/app"

# Instalar dependências de runtime
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -r evolution \
    && useradd -r -g evolution evolution

# Criar diretórios necessários
RUN mkdir -p /app/logs /app/uploads /app/temp && \
    chown -R evolution:evolution /app

# Copiar dependências do stage builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Definir diretório de trabalho
WORKDIR /app

# Copiar código da aplicação
COPY --chown=evolution:evolution . .

# Criar script de inicialização
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
# Aguardar banco de dados\n\
if [ "$DATABASE_URL" ]; then\n\
    echo "Aguardando banco de dados..."\n\
    python -c "\n\
import time\n\
import psycopg2\n\
import os\n\
from urllib.parse import urlparse\n\
\n\
db_url = os.getenv('DATABASE_URL')\n\
if db_url:\n\
    parsed = urlparse(db_url)\n\
    for i in range(30):\n\
        try:\n\
            conn = psycopg2.connect(\n\
                host=parsed.hostname,\n\
                port=parsed.port or 5432,\n\
                user=parsed.username,\n\
                password=parsed.password,\n\
                database=parsed.path[1:]\n\
            )\n\
            conn.close()\n\
            print('Banco conectado!')\n\
            break\n\
        except psycopg2.OperationalError:\n\
            print(f'Tentativa {i+1}/30 - Aguardando banco...')\n\
            time.sleep(2)\n\
    else:\n\
        print('Erro: Não foi possível conectar ao banco')\n\
        exit(1)\n\
"\n\
fi\n\
\n\
# Executar migrações\n\
echo "Executando migrações..."\n\
python -c "\n\
from core.database import init_db\n\
init_db()\n\
print('Migrações concluídas!')\n\
"\n\
\n\
# Iniciar aplicação\n\
echo "Iniciando Evolution API..."\n\
exec uvicorn main:app --host 0.0.0.0 --port $PORT --workers $WORKERS\n\
' > /app/start.sh && chmod +x /app/start.sh

# Mudar para usuário não-root
USER evolution

# Expor porta
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Comando padrão
CMD ["/app/start.sh"]