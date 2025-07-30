# app.py - Sistema C09 Bot para Cloud Run (padrão Sentinela)
"""
Servidor Flask para executar Sistema C09 no Cloud Run.
Baseado no padrão do Sentinela que já funciona.
"""

import os
import json
import threading
import traceback
from flask import Flask, request, jsonify
from datetime import datetime

# Importa sistema C09
try:
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent))
    
    from main import C09Orchestrator
    MAIN_AVAILABLE = True
    print("✅ Sistema C09 importado com sucesso")
except ImportError as e:
    print(f"❌ Erro ao importar main: {e}")
    MAIN_AVAILABLE = False

app = Flask(__name__)

# Estado global da execução
execution_state = {
    "running": False,
    "last_execution": None,
    "last_result": None,
    "error": None,
    "mode": None,
    "start_time": None
}

def execute_c09_async(mode="COMPLETO"):
    """
    Executa sistema C09 em background.
    Padrão similar ao Sentinela.
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
        
        # Executa sistema
        orchestrator = C09Orchestrator()
        sucesso = orchestrator.executar_com_retry(max_tentativas=3)
        
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
        # Status do sistema (como Sentinela)
        return jsonify({
            "service": "Sistema C09 Bot",
            "version": "1.0.0",
            "status": "busy" if execution_state["running"] else "ready",
            "main_available": MAIN_AVAILABLE,
            "execution": execution_state,
            "environment": {
                "K_SERVICE": os.getenv("K_SERVICE", "unknown"),
                "EXECUTION_MODE": os.getenv("EXECUTION_MODE", "COMPLETO"),
                "PORT": os.getenv("PORT", "8080")
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
                "status": "unavailable"
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
            "timestamp": datetime.now().isoformat()
        })

@app.route('/health', methods=['GET'])
def health():
    """Health check obrigatório para Cloud Run."""
    return jsonify({
        "status": "healthy",
        "service": "c09-bot",
        "timestamp": datetime.now().isoformat(),
        "main_available": MAIN_AVAILABLE
    })

@app.route('/status', methods=['GET'])  
def status():
    """Status detalhado (debugging)."""
    return jsonify({
        "service_info": {
            "name": "Sistema C09 Bot",
            "version": "1.0.0",
            "main_available": MAIN_AVAILABLE
        },
        "execution_state": execution_state,
        "environment": {
            "K_SERVICE": os.getenv("K_SERVICE"),
            "EXECUTION_MODE": os.getenv("EXECUTION_MODE"),
            "PORT": os.getenv("PORT"),
            "PROJECT_ID": os.getenv("GOOGLE_CLOUD_PROJECT")
        },
        "system": {
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "working_directory": os.getcwd(),
            "files_present": os.listdir(".")[:10]  # Primeiros 10 arquivos
        }
    })

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
    request.json = {"mode": mode}
    
    return index()  # Reutiliza lógica do POST

if __name__ == '__main__':
    # Configuração para Cloud Run (igual ao Sentinela)
    port = int(os.environ.get('PORT', 8080))
    
    print("=" * 50)
    print("🚀 SISTEMA C09 BOT - INICIANDO")
    print("=" * 50)
    print(f"🌐 Porta: {port}")
    print(f"🔧 Modo: {os.getenv('EXECUTION_MODE', 'COMPLETO')}")
    print(f"📦 Sistema C09: {'✅ Disponível' if MAIN_AVAILABLE else '❌ Indisponível'}")
    print(f"🌍 Environment: {os.getenv('K_SERVICE', 'local')}")
    print("=" * 50)
    
    # Inicia servidor Flask
    app.run(
        host='0.0.0.0',
        port=port,
        debug=False,
        threaded=True
    )