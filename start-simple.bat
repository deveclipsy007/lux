@echo off
REM ========================================
REM Agno SDK Agent Generator - Quick Start
REM ========================================
REM
REM Script simplificado para inicialização rápida
REM (assume que dependências já estão instaladas)
REM
REM Autor: AgnoMaster
REM Data: 2025-01-24
REM ========================================

echo.
echo ========================================
echo  Agno SDK Agent Generator - Quick Start
echo ========================================
echo.

REM Cria diretório de logs se não existir
if not exist "backend\logs" mkdir "backend\logs"

echo Iniciando Backend e Frontend...
echo.

REM Inicia Backend
echo [1/2] Backend (porta 8000)...
start "Agno Backend" cmd /k "cd /d "%~dp0backend" && uvicorn main:app --reload --port 8000"

REM Aguarda 2 segundos
timeout /t 2 /nobreak >nul

REM Inicia Frontend
echo [2/2] Frontend (porta 5500)...
start "Agno Frontend" cmd /k "cd /d "%~dp0frontend" && npx live-server --port=5500 --no-browser"

echo.
echo ========================================
echo  Servicos Iniciados!
echo ========================================
echo.
echo Frontend: http://localhost:5500
echo Backend:  http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo.
echo Abrindo navegador em 3 segundos...
timeout /t 3 /nobreak >nul

REM Abre o navegador
start http://localhost:5500

echo.
echo Para parar os servicos, feche as janelas do terminal.
echo.
pause