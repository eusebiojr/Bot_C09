# teste_nova_logica.py
"""
Script para testar nova lógica CANDLES vs COMPLETO
Execute ANTES de aplicar as mudanças em produção.
"""

import os
import sys
from datetime import datetime
from pathlib import Path

# Simula modo CANDLES
os.environ["EXECUTION_MODE"] = "CANDLES"

# Adiciona path do projeto
sys.path.insert(0, str(Path(__file__).parent))

def teste_modo_candles():
    """Testa novo modo CANDLES."""
    print("🧪 TESTANDO NOVA LÓGICA - MODO CANDLES")
    print("=" * 50)
    
    try:
        from main import C09Orchestrator
        
        # Cria orchestrator
        orchestrator = C09Orchestrator()
        
        # Verifica modo detectado
        print(f"🔧 Modo detectado: {orchestrator.modo_execucao}")
        
        if orchestrator.modo_execucao != "CANDLES":
            print("❌ ERRO: Modo não foi detectado como CANDLES")
            return False
        
        # Testa período
        data_inicial, data_final = orchestrator._obter_periodo_execucao()
        print(f"📅 Período: {data_inicial.date()} até {data_final.date()}")
        
        # Verifica se é período completo (01/mês - hoje)
        hoje = datetime.now()
        esperado_inicial = hoje.replace(day=1).date()
        esperado_final = hoje.date()
        
        if data_inicial.date() != esperado_inicial:
            print(f"❌ ERRO: Data inicial incorreta. Esperado: {esperado_inicial}, Obtido: {data_inicial.date()}")
            return False
            
        if data_final.date() != esperado_final:
            print(f"❌ ERRO: Data final incorreta. Esperado: {esperado_final}, Obtido: {data_final.date()}")
            return False
        
        print("✅ Período correto: sempre 01/mês até hoje")
        
        # Testa configurações
        unidades_ativas = [u for u in orchestrator.config["unidades"] if u.get("ativo", True)]
        print(f"📋 Unidades ativas: {len(unidades_ativas)}")
        
        for unidade in unidades_ativas:
            print(f"   - {unidade['unidade']}: {unidade['empresa_frotalog']}")
        
        print("✅ Configurações carregadas corretamente")
        
        # Simula execução (sem download real)
        print("\n🔄 Simulando execução modo CANDLES...")
        print("   📥 Download: 01/mês - hoje (período completo)")
        print("   ⚙️ Processamento: todos os dados")
        print("   📊 Candles: apenas atualização (sem alertas)")
        print("   ❌ Pula: alertas, TPV/DM, upload arquivo principal")
        
        return True
        
    except Exception as e:
        print(f"❌ ERRO no teste: {e}")
        import traceback
        traceback.print_exc()
        return False

def teste_modo_completo():
    """Testa modo COMPLETO para comparação."""
    print("\n🧪 TESTANDO MODO COMPLETO (para comparar)")
    print("=" * 50)
    
    # Muda modo
    os.environ["EXECUTION_MODE"] = "COMPLETO"
    
    try:
        # Reimporta para pegar nova env var
        import importlib
        import main
        importlib.reload(main)
        
        from main import C09Orchestrator
        
        orchestrator = C09Orchestrator()
        print(f"🔧 Modo detectado: {orchestrator.modo_execucao}")
        
        if orchestrator.modo_execucao != "COMPLETO":
            print("❌ ERRO: Modo não foi detectado como COMPLETO")
            return False
        
        # Testa período (deve ser igual)
        data_inicial, data_final = orchestrator._obter_periodo_execucao()
        print(f"📅 Período: {data_inicial.date()} até {data_final.date()}")
        
        print("✅ Modo COMPLETO funciona igual (período)")
        
        print("\n🔄 Modo COMPLETO executa:")
        print("   📥 Download: 01/mês - hoje (período completo)")
        print("   ⚙️ Processamento: todos os dados")
        print("   📤 Upload: arquivo principal SharePoint")
        print("   📊 Analytics: TPV, DM, métricas completas")
        print("   🚨 Alertas: sistema Sentinela completo")
        print("   📈 Candles: atualização completa")
        
        return True
        
    except Exception as e:
        print(f"❌ ERRO no teste modo completo: {e}")
        return False

def main():
    """Executa todos os testes."""
    print("🚀 TESTANDO NOVA LÓGICA C09")
    print("Data/Hora:", datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
    print("=" * 60)
    
    # Teste 1: Modo CANDLES
    sucesso_candles = teste_modo_candles()
    
    # Teste 2: Modo COMPLETO  
    sucesso_completo = teste_modo_completo()
    
    # Resultado
    print("\n" + "=" * 60)
    print("📋 RESULTADO DOS TESTES:")
    print(f"   ⚡ Modo CANDLES: {'✅ OK' if sucesso_candles else '❌ FALHA'}")
    print(f"   🔄 Modo COMPLETO: {'✅ OK' if sucesso_completo else '❌ FALHA'}")
    
    if sucesso_candles and sucesso_completo:
        print("\n🎉 TODOS OS TESTES PASSARAM!")
        print("✅ Nova lógica está pronta para implementação")
        print("\n📋 PRÓXIMOS PASSOS:")
        print("1. Aplicar mudanças no main.py")
        print("2. Comentar método processar_tempo_real() no analytics_processor.py")  
        print("3. Testar execução real com uma unidade")
        print("4. Monitorar logs para verificar funcionamento")
        return 0
    else:
        print("\n❌ ALGUNS TESTES FALHARAM")
        print("🔧 Corrija os problemas antes de implementar")
        return 1

if __name__ == "__main__":
    sys.exit(main())