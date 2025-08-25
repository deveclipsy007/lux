@echo off
REM ========================================
REM Agno SDK Agent Generator - Startup Script
REM ========================================
REM
REM Este script inicia simultaneamente:
REM - Backend (FastAPI + Uvicorn) na porta 8000
REM - Frontend (Live Server) na porta 5500
REM
REM Autor: AgnoMaster
REM Data: 2025-01-24
REM ========================================

echo.
echo ========================================
echo  Agno SDK Agent Generator - Startup
echo ========================================
echo.
echo Iniciando Backend e Frontend...
echo.

REM Verifica se estamos no diretório correto
if not exist "backend\main.py" (
    echo ERRO: Arquivo backend\main.py nao encontrado!
    echo Certifique-se de executar este script na raiz do projeto.
    pause
    exit /b 1
)

if not exist "frontend\index.html" (
    echo ERRO: Arquivo frontend\index.html nao encontrado!
    echo Certifique-se de executar este script na raiz do projeto.
    pause
    exit /b 1
)

REM Verifica se o Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ERRO: Python nao encontrado no PATH!
    echo Instale o Python e tente novamente.
    pause
    exit /b 1
)

REM Verifica se o Node.js está instalado
node --version >nul 2>&1
if errorlevel 1 (
    echo ERRO: Node.js nao encontrado no PATH!
    echo Instale o Node.js e tente novamente.
    pause
    exit /b 1
)

REM Cria diretório de logs se não existir
if not exist "backend\logs" (
    echo Criando diretorio de logs...
    mkdir "backend\logs"
)

REM Verifica se as dependências do Python estão instaladas
echo Verificando dependencias do Python...
python -c "import fastapi, uvicorn" >nul 2>&1
if errorlevel 1 (
    echo.
    echo AVISO: Dependencias do Python nao encontradas!
    echo Instalando dependencias automaticamente...
    echo.
    pip install -r backend\requirements.txt
    if errorlevel 1 (
        echo ERRO: Falha ao instalar dependencias do Python!
        pause
        exit /b 1
    )
)

REM Verifica se o live-server está instalado globalmente
echo Verificando live-server...
npx live-server --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo AVISO: live-server nao encontrado!
    echo Instalando live-server automaticamente...
    echo.
    npm install -g live-server
    if errorlevel 1 (
        echo ERRO: Falha ao instalar live-server!
        echo Tente instalar manualmente: npm install -g live-server
        pause
        exit /b 1
    )
)

echo.
echo ========================================
echo  Iniciando Servicos...
echo ========================================
echo.

REM Inicia o Backend em uma nova janela
echo [1/2] Iniciando Backend (FastAPI + Uvicorn)...
start "Agno Backend - FastAPI" cmd /k "cd /d "%~dp0backend" && echo Iniciando Backend na porta 8000... && echo. && uvicorn main:app --reload --port 8000 --host 0.0.0.0"

REM Aguarda 3 segundos para o backend inicializar
echo Aguardando backend inicializar...
timeout /t 3 /nobreak >nul

REM Inicia o Frontend em uma nova janela
echo [2/2] Iniciando Frontend (Live Server)...
start "Agno Frontend - Live Server" cmd /k "cd /d "%~dp0frontend" && echo Iniciando Frontend na porta 5500... && echo. && npx live-server --port=5500 --no-browser"

echo.
echo ========================================
echo  Servicos Iniciados com Sucesso!
echo ========================================
echo.
echo Frontend: http://localhost:5500
echo Backend:  http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo Health:   http://localhost:8000/api/health
echo.
echo Para parar os servicos, feche as janelas do terminal
echo ou pressione Ctrl+C em cada uma delas.
echo.
echo Pressione qualquer tecla para abrir o navegador...
pause >nul

REM Abre o navegador com o frontend
start http://localhost:5500

echo.
echo Script finalizado. Os servicos continuam executando
echo nas janelas abertas.
echo.
pause