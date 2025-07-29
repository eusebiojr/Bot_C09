# teste_local.py
"""
Script de teste para validar as modificações do sistema C09.
Testa os dois modos de execução sem fazer downloads reais.
"""

import sys
import os
from pathlib import Path

# Adiciona diretório ao path
sys.path.append(str(Path(__file__).parent))

def testar_modo_candles():
    """Testa modo CANDLES (10 minutos)."""
    print("🧪 TESTANDO MODO CANDLES")
    print("=" * 50)
    
    try:
        # Simula variável de ambiente
        os.environ["EXECUTION_MODE"] = "CANDLES"
        
        from main import C09Orchestrator
        
        # Inicializa orquestrador
        orchestrator = C09Orchestrator()
        
        # Verifica se detectou modo correto
        if orchestrator.modo_execucao == "CANDLES":
            print("✅ Modo CANDLES detectado corretamente")
        else:
            print(f"❌ Esperado CANDLES, obtido {orchestrator.modo_execucao}")
            return False
        
        # Verifica se scraper não foi inicializado (modo rápido)
        if orchestrator.scraper is None:
            print("✅ Scraper não inicializado no modo CANDLES (correto)")
        else:
            print("❌ Scraper foi inicializado no modo CANDLES (incorreto)")
            return False
        
        print("✅ Teste modo CANDLES passou")
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste CANDLES: {e}")
        return False

def testar_modo_completo():
    """Testa modo COMPLETO (1 hora)."""
    print("\n🧪 TESTANDO MODO COMPLETO")
    print("=" * 50)
    
    try:
        # Simula variável de ambiente
        os.environ["EXECUTION_MODE"] = "COMPLETO"
        
        from main import C09Orchestrator
        
        # Inicializa orquestrador
        orchestrator = C09Orchestrator()
        
        # Verifica se detectou modo correto
        if orchestrator.modo_execucao == "COMPLETO":
            print("✅ Modo COMPLETO detectado corretamente")
        else:
            print(f"❌ Esperado COMPLETO, obtido {orchestrator.modo_execucao}")
            return False
        
        # Verifica se scraper foi inicializado
        if orchestrator.scraper is not None:
            print("✅ Scraper inicializado no modo COMPLETO (correto)")
        else:
            print("❌ Scraper não foi inicializado no modo COMPLETO (incorreto)")
            return False
        
        print("✅ Teste modo COMPLETO passou")
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste COMPLETO: {e}")
        return False

def testar_deteccao_argumentos():
    """Testa detecção por argumentos da linha de comando."""
    print("\n🧪 TESTANDO DETECÇÃO POR ARGUMENTOS")
    print("=" * 50)
    
    try:
        # Remove variável de ambiente
        if "EXECUTION_MODE" in os.environ:
            del os.environ["EXECUTION_MODE"]
        
        # Simula argumento da linha de comando
        sys.argv = ["teste_local.py", "CANDLES"]
        
        from main import C09Orchestrator
        
        # Inicializa orquestrador
        orchestrator = C09Orchestrator()
        
        if orchestrator.modo_execucao == "CANDLES":
            print("✅ Detecção por argumentos funcionando")
        else:
            print(f"❌ Esperado CANDLES via args, obtido {orchestrator.modo_execucao}")
            return False
        
        # Restaura sys.argv
        sys.argv = ["teste_local.py"]
        
        print("✅ Teste detecção argumentos passou")
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste argumentos: {e}")
        return False

def testar_analytics_tempo_real():
    """Testa se analytics tempo real está funcionando."""
    print("\n🧪 TESTANDO ANALYTICS TEMPO REAL")
    print("=" * 50)
    
    try:
        from config.settings import carregar_config
        from core.analytics_processor import criar_analytics_processor
        
        # Carrega configuração
        config = carregar_config()
        
        # Cria processor para RRP
        processor = criar_analytics_processor("RRP", config)
        
        # Verifica se método existe
        if hasattr(processor, 'processar_tempo_real'):
            print("✅ Método processar_tempo_real existe")
        else:
            print("❌ Método processar_tempo_real não encontrado")
            return False
        
        print("✅ Teste analytics tempo real passou")
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste analytics: {e}")
        return False

def testar_email_notifier():
    """Testa se sistema de e-mail está funcionando."""
    print("\n🧪 TESTANDO SISTEMA DE E-MAIL")
    print("=" * 50)
    
    try:
        from config.settings import carregar_config
        from core.email_notifier import criar_email_notifier
        
        # Carrega configuração
        config = carregar_config()
        
        # Cria notificador
        notifier = criar_email_notifier(config)
        
        # Verifica se foi inicializado
        if notifier.username:
            print(f"✅ EmailNotifier inicializado para {notifier.username}")
        else:
            print("❌ EmailNotifier não inicializou corretamente")
            return False
        
        # Verifica se templates existem
        if hasattr(notifier, '_gerar_template_alerta_desvio'):
            print("✅ Templates de e-mail disponíveis")
        else:
            print("❌ Templates de e-mail não encontrados")
            return False
        
        print("✅ Teste sistema e-mail passou")
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste e-mail: {e}")
        return False

def main():
    """Executa todos os testes."""
    print("🚀 INICIANDO TESTES DO SISTEMA C09 REFATORADO")
    print("=" * 60)
    
    testes = [
        ("Modo CANDLES", testar_modo_candles),
        ("Modo COMPLETO", testar_modo_completo),
        ("Detecção Argumentos", testar_deteccao_argumentos),
        ("Analytics Tempo Real", testar_analytics_tempo_real),
        ("Sistema E-mail", testar_email_notifier)
    ]
    
    resultados = []
    
    for nome, teste in testes:
        sucesso = teste()
        resultados.append((nome, sucesso))
    
    # Relatório final
    print("\n" + "=" * 60)
    print("📊 RELATÓRIO FINAL DOS TESTES")
    print("=" * 60)
    
    sucessos = 0
    falhas = 0
    
    for nome, sucesso in resultados:
        status = "✅ PASSOU" if sucesso else "❌ FALHOU"
        print(f"{nome:.<30} {status}")
        
        if sucesso:
            sucessos += 1
        else:
            falhas += 1
    
    print(f"\n📈 RESUMO: {sucessos} sucessos, {falhas} falhas")
    
    if falhas == 0:
        print("🎉 TODOS OS TESTES PASSARAM! Sistema pronto para deploy.")
        return True
    else:
        print("⚠️ ALGUNS TESTES FALHARAM. Verifique os erros acima.")
        return False

if __name__ == "__main__":
    sucesso = main()
    sys.exit(0 if sucesso else 1)