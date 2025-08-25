@echo off
REM ========================================
REM Agno SDK Agent Generator - Stop Script
REM ========================================
REM
REM Este script para os serviços do Agno SDK Agent Generator
REM matando os processos do uvicorn e live-server
REM
REM Autor: AgnoMaster
REM Data: 2025-01-24
REM ========================================

echo.
echo ========================================
echo  Agno SDK Agent Generator - Stop
echo ========================================
echo.
echo Parando servicos...
echo.

REM Para processos do uvicorn (Backend)
echo [1/2] Parando Backend (uvicorn)...
taskkill /f /im uvicorn.exe >nul 2>&1
taskkill /f /im python.exe /fi "WINDOWTITLE eq Agno Backend*" >nul 2>&1

REM Para processos do live-server (Frontend)
echo [2/2] Parando Frontend (live-server)...
taskkill /f /im node.exe /fi "WINDOWTITLE eq Agno Frontend*" >nul 2>&1
taskkill /f /im cmd.exe /fi "WINDOWTITLE eq Agno Backend*" >nul 2>&1
taskkill /f /im cmd.exe /fi "WINDOWTITLE eq Agno Frontend*" >nul 2>&1

REM Para processos na porta 8000 e 5500 (backup)
echo Verificando portas 8000 e 5500...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000') do (
    taskkill /f /pid %%a >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5500') do (
    taskkill /f /pid %%a >nul 2>&1
)

echo.
echo ========================================
echo  Servicos Parados!
echo ========================================
echo.
echo Todos os processos relacionados ao Agno SDK
echo Agent Generator foram finalizados.
echo.
echo Pressione qualquer tecla para sair...
pause >nul