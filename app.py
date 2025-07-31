# app.py - Sistema C09 Bot para Cloud Run (OTIMIZADO)
"""
Servidor Flask para executar Sistema C09 no Cloud Run.
VERSÃO CORRIGIDA: Startup otimizado e health checks robustos.
"""

import os
import json
import sys
import signal
import atexit
import threading
import traceback
from flask import Flask, request, jsonify
from datetime import datetime
from pathlib import Path

# Configurações otimizadas para Cloud Run
def setup_signal_handlers():
    """Configura handlers para encerramento graceful (compatível Windows/Linux)."""
    def cleanup_handler(signum, frame):
        print("🔄 Limpando recursos antes de encerrar...")
        
    # SIGTERM existe em ambos os sistemas
    signal.signal(signal.SIGTERM, cleanup_handler)
    
    # SIGALRM só existe no Unix/Linux - pula no Windows
    if hasattr(signal, 'SIGALRM'):
        def timeout_handler(signum, frame):
            print("⏱️ Timeout de inicialização - forçando startup")
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(30)  # Timeout de 30s para inicialização
        print("✅ Signal handlers Unix configurados")
    else:
        print("ℹ️ Windows detectado - signal handlers limitados")
    
    atexit.register(lambda: print("✅ App finalizado"))

# Configuração inicial
setup_signal_handlers()

# Importa sistema C09 com tratamento de erro
try:
    sys.path.append(str(Path(__file__).parent))
    from main import C09Orchestrator
    MAIN_AVAILABLE = True
    print("✅ Sistema C09 importado com sucesso")
except ImportError as e:
    print(f"❌ Erro ao importar main: {e}")
    MAIN_AVAILABLE = False
except Exception as e:
    print(f"⚠️ Erro inesperado no import: {e}")
    MAIN_AVAILABLE = False

app = Flask(__name__)

# Estado global da execução
execution_state = {
    "running": False,
    "last_execution": None,
    "last_result": None,
    "error": None,
    "mode": None,
    "start_time": None,
    "startup_time": datetime.now().isoformat()
}

def execute_c09_async(mode="COMPLETO"):
    """
    Executa sistema C09 em background.
    Otimizado para Cloud Run com timeouts e error handling.
    """
    global execution_state
    
    try:
        execution_state.update({
            "running": True,
            "error": None,
            "mode": mode,
            "start_time": datetime.now().isoformat()
        })
        
        print(f"🚀 [C09] Iniciando execução - Modo: {mode}")
        
        if not MAIN_AVAILABLE:
            raise Exception("Sistema C09 não disponível - erro no import do main.py")
        
        # Define modo via env var (como C09 espera)
        os.environ["EXECUTION_MODE"] = mode.upper()
        
        # Executa sistema com timeout reduzido para Cloud Run
        orchestrator = C09Orchestrator()
        sucesso = orchestrator.executar_com_retry(max_tentativas=2)  # Reduzido
        
        # Atualiza estado
        execution_state.update({
            "running": False,
            "last_execution": datetime.now().isoformat(),
            "last_result": "SUCCESS" if sucesso else "FAILED",
            "error": None if sucesso else "Execução falhou (veja logs)"
        })
        
        resultado = "✅ SUCESSO" if sucesso else "❌ FALHA"
        print(f"🏁 [C09] Execução finalizada - {resultado}")
        
    except Exception as e:
        error_msg = f"{str(e)}\n{traceback.format_exc()}"
        
        execution_state.update({
            "running": False,
            "last_execution": datetime.now().isoformat(),
            "last_result": "ERROR",
            "error": error_msg
        })
        
        print(f"💥 [C09] ERRO na execução: {e}")
        print(f"📋 [C09] Stack trace: {traceback.format_exc()}")

@app.route('/', methods=['GET', 'POST'])
def index():
    """
    Endpoint principal - padrão Cloud Run.
    GET: Status do sistema
    POST: Executa sistema C09
    """
    
    if request.method == 'GET':
        # Status do sistema
        return jsonify({
            "service": "Sistema C09 Bot",
            "version": "1.0.1",
            "status": "busy" if execution_state["running"] else "ready",
            "main_available": MAIN_AVAILABLE,
            "execution": execution_state,
            "environment": {
                "K_SERVICE": os.getenv("K_SERVICE", "unknown"),
                "EXECUTION_MODE": os.getenv("EXECUTION_MODE", "COMPLETO"),
                "PORT": os.getenv("PORT", "8080"),
                "startup_time": execution_state["startup_time"]
            }
        })
    
    elif request.method == 'POST':
        # Executa sistema C09
        if execution_state["running"]:
            return jsonify({
                "error": "Sistema C09 já está executando",
                "status": "busy",
                "current_execution": execution_state
            }), 429
        
        if not MAIN_AVAILABLE:
            return jsonify({
                "error": "Sistema C09 não disponível - problema no import",
                "status": "unavailable",
                "details": "Verifique logs de inicialização"
            }), 503
        
        # Determina modo de execução
        try:
            data = request.get_json(silent=True) or {}
            mode = data.get("mode", os.getenv("EXECUTION_MODE", "COMPLETO")).upper()
            
            if mode not in ["COMPLETO", "CANDLES"]:
                mode = "COMPLETO"
                
        except Exception:
            mode = "COMPLETO"
        
        # Executa em thread separada (não bloqueia Cloud Run)
        thread = threading.Thread(
            target=execute_c09_async,
            args=(mode,),
            daemon=True,
            name=f"C09-{mode}-{datetime.now().strftime('%H%M%S')}"
        )
        thread.start()
        
        return jsonify({
            "message": f"Sistema C09 iniciado com sucesso",
            "mode": mode,
            "status": "started",
            "thread": thread.name,
            "timestamp": datetime.now().isoformat(),
            "estimated_duration": "15-30min" if mode == "COMPLETO" else "2-5min"
        })

@app.route('/health', methods=['GET'])
def health():
    """Health check otimizado para Cloud Run startup."""
    try:
        # Cancela timeout de inicialização (só no Unix/Linux)
        if hasattr(signal, 'alarm'):
            signal.alarm(0)
        
        # Health check que responde rapidamente
        health_data = {
            "status": "healthy",
            "service": "c09-bot", 
            "timestamp": datetime.now().isoformat(),
            "main_available": MAIN_AVAILABLE,
            "ready": True,
            "uptime_seconds": (datetime.now() - datetime.fromisoformat(execution_state["startup_time"])).total_seconds(),
            "platform": "windows" if os.name == 'nt' else "unix"
        }
        
        # Teste básico de funcionalidade
        if MAIN_AVAILABLE:
            health_data["system_status"] = "operational"
        else:
            health_data["system_status"] = "degraded"
            health_data["warning"] = "Main system not available"
        
        return jsonify(health_data), 200
        
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
            "ready": False
        }), 503

@app.route('/status', methods=['GET'])  
def status():
    """Status detalhado (debugging)."""
    try:
        return jsonify({
            "service_info": {
                "name": "Sistema C09 Bot",
                "version": "1.0.1",
                "main_available": MAIN_AVAILABLE,
                "startup_time": execution_state["startup_time"]
            },
            "execution_state": execution_state,
            "environment": {
                "K_SERVICE": os.getenv("K_SERVICE"),
                "EXECUTION_MODE": os.getenv("EXECUTION_MODE"),
                "PORT": os.getenv("PORT"),
                "PROJECT_ID": os.getenv("GOOGLE_CLOUD_PROJECT"),
                "CHROME_BIN": os.getenv("CHROME_BIN"),
                "PYTHONPATH": os.getenv("PYTHONPATH")
            },
            "system": {
                "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                "working_directory": os.getcwd(),
                "files_present": sorted(os.listdir("."))[:15],  # Primeiros 15 arquivos
                "memory_info": _get_memory_info()
            }
        })
    except Exception as e:
        return jsonify({
            "error": f"Erro ao obter status: {e}",
            "timestamp": datetime.now().isoformat()
        }), 500

def _get_memory_info():
    """Obtém informações de memória se disponível."""
    try:
        import psutil
        memory = psutil.virtual_memory()
        return {
            "total_gb": round(memory.total / (1024**3), 2),
            "available_gb": round(memory.available / (1024**3), 2),
            "percent_used": memory.percent
        }
    except ImportError:
        return {"status": "psutil not available"}
    except Exception as e:
        return {"error": str(e)}

@app.route('/trigger/<mode>', methods=['POST'])
def trigger_execution(mode):
    """
    Endpoint específico para Cloud Scheduler.
    /trigger/completo - Execução completa
    /trigger/candles - Execução candles
    """
    mode = mode.upper()
    
    if mode not in ["COMPLETO", "CANDLES"]:
        return jsonify({
            "error": f"Modo inválido: {mode}",
            "valid_modes": ["COMPLETO", "CANDLES"]
        }), 400
    
    # Simula POST request
    os.environ["EXECUTION_MODE"] = mode
    
    # Cria mock request
    class MockRequest:
        def get_json(self, silent=True):
            return {"mode": mode}
    
    original_request = request
    request.json = {"mode": mode}
    
    try:
        return index()  # Reutiliza lógica do POST
    finally:
        pass

# Função de startup otimizada
def startup_checks():
    """Executa verificações de startup."""
    print("🔍 Executando verificações de startup...")
    
    # Verifica Chrome
    chrome_paths = [
        "/usr/bin/google-chrome",
        "/usr/bin/google-chrome-stable", 
        "/usr/bin/chromium"
    ]
    
    chrome_found = False
    for path in chrome_paths:
        if os.path.exists(path):
            print(f"✅ Chrome encontrado: {path}")
            chrome_found = True
            break
    
    if not chrome_found:
        print("⚠️ Chrome não encontrado - pode causar problemas")
    
    # Verifica credenciais
    required_vars = ["FROTA_USER", "SP_USER"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"⚠️ Variáveis faltando: {missing_vars}")
    else:
        print("✅ Credenciais básicas configuradas")
    
    print("✅ Startup checks concluídos")

if __name__ == '__main__':
    # Configuração otimizada para Cloud Run
    port = int(os.environ.get('PORT', 8080))
    
    print("=" * 60)
    print("🚀 SISTEMA C09 BOT - CLOUD RUN STARTUP v1.0.1")
    print("=" * 60)
    print(f"🌐 Porta: {port}")
    print(f"🔧 Modo: {os.getenv('EXECUTION_MODE', 'COMPLETO')}")
    print(f"📦 Sistema C09: {'✅ Disponível' if MAIN_AVAILABLE else '❌ Indisponível'}")
    print(f"🌍 Environment: {os.getenv('K_SERVICE', 'local')}")
    print(f"🕐 Startup: {execution_state['startup_time']}")
    print("=" * 60)
    
    # Executa verificações de startup
    startup_checks()
    
    try:
        print(f"🚀 Iniciando servidor Flask na porta {port}...")
        
        # Configurações otimizadas para Cloud Run
        app.run(
            host='0.0.0.0',
            port=port,
            debug=False,
            threaded=True,
            use_reloader=False,  # Importante para Cloud Run
            processes=1  # Single process para evitar problemas
        )
        
    except Exception as e:
        print(f"💥 ERRO CRÍTICO no startup: {e}")
        traceback.print_exc()
        sys.exit(1)