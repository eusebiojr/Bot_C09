# app.py - HTTP Server para Cloud Run
"""
Servidor HTTP que recebe requests do Cloud Scheduler e executa main.py
"""

import os
import subprocess
import json
import traceback
from datetime import datetime
from flask import Flask, request, jsonify
import logging

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configurações Cloud Run
PORT = int(os.environ.get('PORT', 8080))
K_SERVICE = os.environ.get('K_SERVICE')  # Detecta automaticamente se está no Cloud Run


@app.route('/')
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "C09 Processing System",
        "timestamp": datetime.now().isoformat(),
        "environment": "cloud" if K_SERVICE else "local"
    })


@app.route('/health')
def health():
    """Health check para Cloud Run"""
    return "OK", 200


@app.route('/trigger', methods=['POST', 'GET'])
def trigger_processing():
    """
    Endpoint principal que executa o processamento C09.
    Chamado pelo Cloud Scheduler.
    """
    start_time = datetime.now()
    logger.info(f"🚀 Iniciando processamento C09 - {start_time}")
    
    try:
        # Executa main.py como subprocess COM TIMEOUT E ENCODING
        logger.info("📋 Iniciando subprocess main.py...")
        
        result = subprocess.run(
            ['python', 'main.py'],
            capture_output=True,
            text=True,
            encoding='utf-8',  # FORÇA UTF-8
            errors='replace',  # SUBSTITUI caracteres problemáticos
            timeout=600,  # 10 minutos timeout
            cwd=os.getcwd()
        )
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Prepara resposta
        response_data = {
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": duration,
            "return_code": result.returncode,
            "success": result.returncode == 0
        }
        
        if result.returncode == 0:
            logger.info(f"✅ Processamento concluído com sucesso - {duration:.1f}s")
            response_data["message"] = "Processamento concluído com sucesso"
            
            # CORREÇÃO: Verificar se stdout existe antes de acessar
            if result.stdout:
                response_data["stdout"] = result.stdout[-1000:]  # Últimas 1000 chars
            else:
                response_data["stdout"] = "Nenhuma saída capturada"
                
            return jsonify(response_data), 200
            
        else:
            logger.error(f"❌ Processamento falhou - código {result.returncode}")
            
            # CORREÇÃO: Verificar se stderr/stdout existem
            if result.stderr:
                logger.error(f"📄 STDERR: {result.stderr}")
                response_data["stderr"] = result.stderr[-2000:]
            else:
                response_data["stderr"] = "Nenhum erro capturado"
                
            if result.stdout:
                logger.error(f"📄 STDOUT: {result.stdout}")
                response_data["stdout"] = result.stdout[-1000:]
            else:
                response_data["stdout"] = "Nenhuma saída capturada"
            
            response_data["message"] = "Processamento falhou"
            
            # Enviar alerta por e-mail (se configurado)
            try:
                from core.email_notifier import EmailNotifier
                from config.settings import ConfigLoader
                
                config_loader = ConfigLoader()
                config = config_loader.carregar_configuracao()
                
                notifier = EmailNotifier(config)
                notifier.enviar_falha_sistema(
                    erro=f"Código de saída: {result.returncode}",
                    contexto=result.stderr,
                    timestamp=start_time
                )
            except Exception as e:
                logger.warning(f"⚠️ Não foi possível enviar alerta: {e}")
            
            return jsonify(response_data), 500
            
    except subprocess.TimeoutExpired:
        logger.error("⏰ TIMEOUT: main.py travou por mais de 10 minutos")
        logger.error("🔍 Possíveis causas: ChromeDriver travado, download infinito, input aguardando")
        
        return jsonify({
            "error": "timeout",
            "message": "main.py travou - processo interrompido após 10 minutos",
            "duration_seconds": 600,
            "troubleshooting": [
                "Verificar se ChromeDriver está funcionando",
                "Testar main.py diretamente: python main.py",
                "Verificar se há prompts aguardando input"
            ]
        }), 408
        
    except Exception as e:
        logger.error(f"💥 Erro inesperado: {e}")
        return jsonify({
            "error": "unexpected_error",
            "message": str(e),
            "traceback": traceback.format_exc()
        }), 500


@app.route('/status')
def status():
    """Endpoint para verificar status atual"""
    return jsonify({
        "system": "C09 Processing System",
        "environment": "cloud" if K_SERVICE else "local",
        "python_version": subprocess.check_output(['python', '--version'], text=True).strip(),
        "chrome_available": check_chrome_available(),
        "timestamp": datetime.now().isoformat()
    })


def check_chrome_available():
    """Verifica se Chrome está disponível"""
    try:
        result = subprocess.run(['google-chrome', '--version'], 
                              capture_output=True, text=True, timeout=5)
        return result.returncode == 0
    except:
        return False


if __name__ == '__main__':
    # Configuração para Cloud Run
    logger.info(f"🌐 Iniciando servidor HTTP na porta {PORT}")
    logger.info(f"🔧 Ambiente: {'Cloud Run' if K_SERVICE else 'Local'}")
    
    app.run(
        host='0.0.0.0',
        port=PORT,
        debug=False  # Nunca debug em produção
    )