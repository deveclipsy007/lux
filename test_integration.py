#!/usr/bin/env python3
"""
Script de teste para integração WhatsApp com Evolution API

Este script testa:
1. Conexão com Evolution API
2. Criação de instância WhatsApp
3. Obtenção de QR Code
4. Configuração de webhook
5. Envio de mensagem de teste

Autor: Agno SDK Agent Generator
Data: 2025-01-25
"""

import asyncio
import json
import sys
import os
from pathlib import Path

# Adiciona o diretório backend ao path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

from services.evolution import EvolutionService
try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings

class TestSettings(BaseSettings):
    """Configurações para teste"""
    evolution_base_url: str = "https://evolution.agentecortex.com"
    evolution_api_key: str = "e464af0bf64bbd059aa777d5cded286e"
    evolution_default_instance: str = "test-agno-agent"

async def test_evolution_integration():
    """
    Testa integração completa com Evolution API
    """
    print("INICIANDO TESTES DE INTEGRACAO WHATSAPP...")
    print("=" * 50)
    
    settings = TestSettings()
    evolution = EvolutionService(settings)
    
    try:
        # Teste 1: Conexão com API
        print("\n[1] Testando conexão com Evolution API...")
        connection_test = await evolution.test_connection()
        print(f"[OK] Conexão OK: {connection_test}")
        
        # Teste 2: Listar instâncias existentes
        print("\n[2] Listando instâncias existentes...")
        instances = await evolution.list_instances()
        print(f"[INFO] Instâncias encontradas: {len(instances)}")
        for instance in instances[:3]:  # Mostra apenas as primeiras 3
            name = instance.get('name', 'N/A')
            status = instance.get('connectionStatus', 'N/A')
            print(f"   - {name} ({status})")
            print(f"     DEBUG: {list(instance.keys()) if isinstance(instance, dict) else 'Not a dict'}")
        
        # Teste 3: Usar instância existente (erro 403 para criar nova)
        test_instance = None
        connecting_instance = None
        
        # Procura por instância em "connecting" para testar QR Code
        for instance in instances:
            if instance.get('connectionStatus') == 'connecting':
                connecting_instance = instance
                break
        
        if connecting_instance:
            test_instance = connecting_instance.get('name')
            print(f"\n[3] Usando instância em connecting: {test_instance}")
            print(f"[INFO] Status atual: {connecting_instance.get('connectionStatus', 'UNKNOWN')}")
        elif instances:
            test_instance = instances[0].get('name', settings.evolution_default_instance)
            print(f"\n[3] Usando primeira instância: {test_instance}")
            print(f"[INFO] Status atual: {instances[0].get('connectionStatus', 'UNKNOWN')}")
        else:
            print(f"\n[3] Tentando criar instância de teste: {settings.evolution_default_instance}")
            try:
                instance_result = await evolution.create_instance(settings.evolution_default_instance)
                test_instance = settings.evolution_default_instance
                print(f"[OK] Instância criada: {instance_result.get('instanceName', 'N/A')}")
            except Exception as e:
                print(f"[WARN] Erro ao criar instância (usando primeira existente): {e}")
                test_instance = instances[0].get('name') if instances else settings.evolution_default_instance
        
        # Teste 4: Obter QR Code
        print(f"\n[4] Obtendo QR Code para pareamento da instância: {test_instance}")
        qr_result = await evolution.get_qr_code(test_instance)
        if qr_result and qr_result.get("qr"):
            print("[OK] QR Code obtido com sucesso!")
            print(f"   Tamanho: {len(qr_result['qr'])} caracteres")
            
            # Salva QR Code em arquivo para visualização
            qr_file = Path(__file__).parent / "qr_code.txt"
            with open(qr_file, "w") as f:
                f.write(qr_result["qr"])
            print(f"   QR Code salvo em: {qr_file}")
        else:
            print("[WARN] QR Code não disponível (pode já estar conectado)")
        
        # Teste 5: Verificar status da instância
        print(f"\n[5] Verificando status da instância: {test_instance}")
        status_result = await evolution.get_connection_state(test_instance)
        print(f"[INFO] Status: {status_result.get('state', 'UNKNOWN')}")
        if status_result.get('phone_number'):
            print(f"[INFO] Número: {status_result['phone_number']}")
        
        # Teste 6: Configurar webhook
        print(f"\n[6] Configurando webhook para: {test_instance}")
        webhook_url = f"https://webhook.site/unique-id/{test_instance}"  # Using webhook.site for testing
        webhook_result = await evolution.set_webhook(test_instance, webhook_url)
        if webhook_result:
            print(f"[OK] Webhook configurado: {webhook_url}")
        else:
            print("[WARN] Falha ao configurar webhook")
        
        print("\n" + "=" * 50)
        print("[SUCCESS] Todos os testes executados!")
        print("\nProximos passos:")
        print("1. Escaneie o QR Code salvo em qr_code.txt com seu WhatsApp")
        print("2. Aguarde a conexão ser estabelecida")
        print("3. Configure um webhook público para receber mensagens")
        print("4. Teste o envio de mensagens")
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Erro durante os testes: {e}")
        return False

async def test_message_sending():
    """
    Testa envio de mensagem (apenas se já conectado)
    """
    settings = TestSettings()
    evolution = EvolutionService(settings)
    
    try:
        # Verifica se a instância está conectada
        status = await evolution.get_connection_state(settings.evolution_default_instance)
        
        if status.get('state') in ['open', 'connected']:
            print(f"\n[INFO] Instância conectada! Estado: {status['state']}")
            
            # Solicita número de teste
            test_number = input("\n[INPUT] Digite um número para teste (formato: 5511999999999): ")
            if not test_number:
                print("[ERROR] Número não fornecido. Teste de mensagem cancelado.")
                return
            
            # Envia mensagem de teste
            message = "Olá! Esta é uma mensagem de teste do Agno Agent Generator.\n\nSua integração WhatsApp está funcionando!"
            
            print(f"[SENDING] Enviando mensagem de teste para {test_number}...")
            result = await evolution.send_message(
                instance_id=settings.evolution_default_instance,
                to=test_number,
                message=message
            )
            
            if result:
                print("[OK] Mensagem enviada com sucesso!")
                print(f"   ID: {result.get('message_id', 'N/A')}")
            else:
                print("[ERROR] Falha ao enviar mensagem")
                
        else:
            print(f"[WARN] Instância não conectada. Estado atual: {status.get('state', 'UNKNOWN')}")
            print("Escaneie o QR Code primeiro para conectar o WhatsApp.")
    
    except Exception as e:
        print(f"[ERROR] Erro ao testar envio de mensagem: {e}")

def main():
    """
    Função principal
    """
    print("Agno SDK Agent Generator - Teste de Integração WhatsApp")
    print("Este script testa a integração com a Evolution API")
    
    if len(sys.argv) > 1 and sys.argv[1] == "--send-test":
        # Modo de teste de envio de mensagem
        asyncio.run(test_message_sending())
    else:
        # Modo de teste completo
        asyncio.run(test_evolution_integration())

if __name__ == "__main__":
    main()