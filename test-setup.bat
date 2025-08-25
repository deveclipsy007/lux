@echo off
REM ========================================
REM Agno SDK Agent Generator - Setup Test
REM ========================================
REM
REM Script para testar se o ambiente está
REM configurado corretamente antes da execução
REM
REM Autor: AgnoMaster
REM Data: 2025-01-24
REM ========================================

echo.
echo ========================================
echo  Agno SDK Agent Generator - Setup Test
echo ========================================
echo.
echo Verificando ambiente de desenvolvimento...
echo.

set "ERRORS=0"

REM Verifica se estamos no diretório correto
echo [1/8] Verificando estrutura do projeto...
if not exist "backend\main.py" (
    echo   ❌ ERRO: backend\main.py nao encontrado!
    set /a ERRORS+=1
) else (
    echo   ✅ backend\main.py encontrado
)

if not exist "frontend\index.html" (
    echo   ❌ ERRO: frontend\index.html nao encontrado!
    set /a ERRORS+=1
) else (
    echo   ✅ frontend\index.html encontrado
)

if not exist "backend\requirements.txt" (
    echo   ❌ ERRO: backend\requirements.txt nao encontrado!
    set /a ERRORS+=1
) else (
    echo   ✅ backend\requirements.txt encontrado
)

echo.
echo [2/8] Verificando Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo   ❌ ERRO: Python nao encontrado no PATH!
    echo   📋 Instale Python 3.8+ e adicione ao PATH
    set /a ERRORS+=1
) else (
    for /f "tokens=2" %%i in ('python --version 2^>^&1') do (
        echo   ✅ Python %%i encontrado
    )
)

echo.
echo [3/8] Verificando Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo   ❌ ERRO: Node.js nao encontrado no PATH!
    echo   📋 Instale Node.js 16+ e adicione ao PATH
    set /a ERRORS+=1
) else (
    for /f %%i in ('node --version 2^>^&1') do (
        echo   ✅ Node.js %%i encontrado
    )
)

echo.
echo [4/8] Verificando npm...
npm --version >nul 2>&1
if errorlevel 1 (
    echo   ❌ ERRO: npm nao encontrado!
    echo   📋 npm geralmente vem com Node.js
    set /a ERRORS+=1
) else (
    for /f %%i in ('npm --version 2^>^&1') do (
        echo   ✅ npm %%i encontrado
    )
)

echo.
echo [5/8] Verificando pip...
pip --version >nul 2>&1
if errorlevel 1 (
    echo   ❌ ERRO: pip nao encontrado!
    echo   📋 pip geralmente vem com Python
    set /a ERRORS+=1
) else (
    for /f "tokens=2" %%i in ('pip --version 2^>^&1') do (
        echo   ✅ pip %%i encontrado
    )
)

echo.
echo [6/8] Verificando dependencias Python...
python -c "import fastapi" >nul 2>&1
if errorlevel 1 (
    echo   ⚠️  FastAPI nao instalado (sera instalado automaticamente)
) else (
    echo   ✅ FastAPI encontrado
)

python -c "import uvicorn" >nul 2>&1
if errorlevel 1 (
    echo   ⚠️  Uvicorn nao instalado (sera instalado automaticamente)
) else (
    echo   ✅ Uvicorn encontrado
)

echo.
echo [7/8] Verificando live-server...
npx live-server --version >nul 2>&1
if errorlevel 1 (
    echo   ⚠️  live-server nao instalado (sera instalado automaticamente)
) else (
    echo   ✅ live-server encontrado
)

echo.
echo [8/8] Verificando portas...
netstat -an | findstr ":8000" >nul 2>&1
if not errorlevel 1 (
    echo   ⚠️  Porta 8000 em uso (execute stop.bat se necessario)
) else (
    echo   ✅ Porta 8000 disponivel
)

netstat -an | findstr ":5500" >nul 2>&1
if not errorlevel 1 (
    echo   ⚠️  Porta 5500 em uso (execute stop.bat se necessario)
) else (
    echo   ✅ Porta 5500 disponivel
)

echo.
echo ========================================
echo  Resultado do Teste
echo ========================================
echo.

if %ERRORS% equ 0 (
    echo ✅ SUCESSO: Ambiente configurado corretamente!
    echo.
    echo 🚀 Proximos passos:
    echo    1. Configure .env (copie de .env.example)
    echo    2. Execute start.bat para primeira inicializacao
    echo    3. Ou execute start-simple.bat para uso diario
    echo.
    echo 🌐 URLs que estarao disponiveis:
    echo    Frontend: http://localhost:5500
    echo    Backend:  http://localhost:8000
    echo    API Docs: http://localhost:8000/docs
    echo.
) else (
    echo ❌ ERRO: %ERRORS% problema(s) encontrado(s)!
    echo.
    echo 🔧 Corrija os erros acima antes de continuar.
    echo.
    echo 📋 Guia de instalacao:
    echo    Python: https://python.org/downloads/
    echo    Node.js: https://nodejs.org/downloads/
    echo.
)

echo Pressione qualquer tecla para sair...
pause >nul