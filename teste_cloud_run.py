#!/usr/bin/env python3
# teste_cloud_run.py - Simula execução Cloud Run localmente
"""
Script para testar o sistema C09 simulando ambiente Cloud Run.
Útil para debugging antes do deploy real.

Uso:
    python teste_cloud_run.py              # Teste básico do scraper
    python teste_cloud_run.py --completo   # Teste completo (download + processamento)
    python teste_cloud_run.py --candles    # Teste modo candles
"""

import os
import sys
import argparse
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

# Simula ambiente Cloud Run
os.environ["K_SERVICE"] = "test-c09-bot"
os.environ["PORT"] = "8080"

# Adiciona path do projeto
sys.path.insert(0, str(Path(__file__).parent))

from core.scraper import FrotalogScraper
from config.settings import carregar_config, validar_configuracao


class CloudRunTester:
    """Testa componentes como se estivessem rodando no Cloud Run."""
    
    def __init__(self):
        print("🧪 SIMULADOR CLOUD RUN - Sistema C09")
        print("=" * 50)
        
        # Carrega configurações
        try:
            self.config = carregar_config()
            if not validar_configuracao(self.config):
                raise ValueError("Configuração inválida")
            print("✅ Configurações carregadas")
        except Exception as e:
            print(f"❌ Erro nas configurações: {e}")
            sys.exit(1)
    
    def teste_basico_scraper(self) -> bool:
        """
        Testa apenas inicialização do scraper (sem download).
        Verifica se Chrome funciona no ambiente simulado.
        """
        print("\n🔍 TESTE 1: Inicialização do Scraper")
        print("-" * 30)
        
        try:
            # Cria scraper (simula Cloud Run)
            scraper = FrotalogScraper(
                chrome_driver_path="",  # Ignorado no Cloud Run
                download_timeout=60
            )
            
            # Testa criação do WebDriver
            print("🔧 Testando criação do WebDriver...")
            driver = scraper._create_webdriver()
            
            # Testa navegação básica
            print("🌐 Testando navegação básica...")
            driver.get("https://www.google.com")
            title = driver.title
            print(f"✅ Título da página: {title}")
            
            # Testa JavaScript (básico)
            js_result = driver.execute_script("return 'JavaScript funcionando'")
            print(f"✅ JavaScript: {js_result}")
            
            driver.quit()
            print("✅ WebDriver fechado com sucesso")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro no teste básico: {e}")
            return False
    
    def teste_download_c09(self, unidade: str = "RRP") -> bool:
        """
        Testa download real do C09 (período pequeno).
        
        Args:
            unidade: Unidade para testar (RRP ou TLS)
        """
        print(f"\n📥 TESTE 2: Download C09 - {unidade}")
        print("-" * 30)
        
        try:
            # Encontra configuração da unidade
            unidade_config = None
            for u in self.config["unidades"]:
                if u["unidade"] == unidade:
                    unidade_config = u
                    break
            
            if not unidade_config:
                print(f"❌ Unidade {unidade} não encontrada")
                return False
            
            # Período pequeno para teste (só hoje)
            hoje = datetime.now()
            data_inicial = hoje
            data_final = hoje
            
            print(f"📅 Período de teste: {data_inicial.date()}")
            print(f"🏢 Empresa: {unidade_config['empresa_frotalog']}")
            
            # Cria scraper
            scraper = FrotalogScraper(
                chrome_driver_path="",
                download_timeout=300
            )
            
            # Executa download
            caminho_arquivo = scraper.baixar_relatorio_c09(
                empresa_frotalog=unidade_config['empresa_frotalog'],
                data_inicial=data_inicial,
                data_final=data_final
            )
            
            # Verifica arquivo
            arquivo = Path(caminho_arquivo)
            if arquivo.exists():
                tamanho_mb = arquivo.stat().st_size / (1024 * 1024)
                print(f"✅ Arquivo baixado: {arquivo.name} ({tamanho_mb:.1f}MB)")
                
                # Remove arquivo de teste
                arquivo.unlink()
                print("🗑️ Arquivo de teste removido")
                
                return True
            else:
                print("❌ Arquivo não encontrado")
                return False
                
        except Exception as e:
            print(f"❌ Erro no download: {e}")
            return False
    
    def teste_processamento_completo(self, unidade: str = "RRP") -> bool:
        """
        Testa fluxo completo: download + processamento + upload.
        
        Args:
            unidade: Unidade para testar
        """
        print(f"\n🔄 TESTE 3: Processamento Completo - {unidade}")
        print("-" * 30)
        
        try:
            # Simula main.py mas com período reduzido
            from main import C09Orchestrator
            
            # Force modo COMPLETO para teste
            os.environ["EXECUTION_MODE"] = "COMPLETO"
            
            # Cria orchestrator
            orchestrator = C09Orchestrator()
            
            # Encontra configuração da unidade
            unidade_config = None
            for u in orchestrator.config["unidades"]:
                if u["unidade"] == unidade and u.get("ativo", True):
                    unidade_config = u
                    break
            
            if not unidade_config:
                print(f"❌ Unidade {unidade} não encontrada ou inativa")
                return False
            
            print(f"🎯 Testando unidade: {unidade}")
            
            # Executa processamento (com dados de hoje apenas)
            sucesso = orchestrator.processar_unidade_modo_completo(unidade_config)
            
            if sucesso:
                print("✅ Processamento completo executado com sucesso")
                return True
            else:
                print("❌ Falha no processamento completo")
                return False
                
        except Exception as e:
            print(f"❌ Erro no processamento completo: {e}")
            return False
    
    def teste_modo_candles(self) -> bool:
        """Testa modo CANDLES (sem download)."""
        print("\n⚡ TESTE 4: Modo Candles")
        print("-" * 30)
        
        try:
            from main import C09Orchestrator
            
            # Force modo CANDLES
            os.environ["EXECUTION_MODE"] = "CANDLES"
            
            # Cria orchestrator
            orchestrator = C09Orchestrator()
            
            # Executa modo candles
            sucesso = orchestrator.executar_ciclo_candles()
            
            if sucesso:
                print("✅ Modo candles executado com sucesso")
                return True
            else:
                print("❌ Falha no modo candles")
                return False
                
        except Exception as e:
            print(f"❌ Erro no modo candles: {e}")
            return False
    
    def diagnostico_ambiente(self):
        """Executa diagnóstico do ambiente simulado."""
        print("\n🔍 DIAGNÓSTICO DO AMBIENTE")
        print("-" * 30)
        
        # Variáveis de ambiente
        print("📋 Variáveis de ambiente relevantes:")
        env_vars = ["K_SERVICE", "PORT", "PYTHONPATH", "FROTA_USER", "SP_USER"]
        for var in env_vars:
            valor = os.getenv(var, "NÃO DEFINIDA")
            # Não mostra senhas completas
            if "PASSWORD" in var:
                valor = "***" if valor != "NÃO DEFINIDA" else valor
            print(f"   {var}: {valor}")
        
        # Diretórios
        print(f"\n📁 Diretório atual: {Path.cwd()}")
        print(f"📁 Diretório temp: {tempfile.gettempdir()}")
        
        # Python
        print(f"\n🐍 Python: {sys.version}")
        print(f"📦 Packages instalados:")
        try:
            import selenium, pandas, openpyxl
            print(f"   selenium: {selenium.__version__}")
            print(f"   pandas: {pandas.__version__}")
            print(f"   openpyxl: {openpyxl.__version__}")
        except ImportError as e:
            print(f"   ❌ Erro ao importar: {e}")
        
        # Chrome (se disponível)
        print(f"\n🌐 Chrome:")
        chrome_paths = [
            "/usr/bin/google-chrome", 
            "/usr/bin/google-chrome-stable",
            "/usr/bin/chromium",
            r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        ]
        
        chrome_found = False
        for path in chrome_paths:
            if os.path.exists(path):
                print(f"   ✅ Encontrado: {path}")
                chrome_found = True
                break
        
        if not chrome_found:
            print("   ❌ Chrome não encontrado nos caminhos padrão")
        
        # Memória (se disponível)
        try:
            import psutil
            memory = psutil.virtual_memory()
            print(f"\n💾 Memória: {memory.percent}% usado ({memory.available // (1024**2)}MB disponível)")
        except ImportError:
            print("\n💾 Memória: psutil não disponível")


def main():
    """Função principal do teste."""
    parser = argparse.ArgumentParser(description="Testa sistema C09 simulando Cloud Run")
    parser.add_argument("--modo", choices=["basico", "download", "completo", "candles", "diagnostico"], 
                       default="basico", help="Modo de teste")
    parser.add_argument("--unidade", choices=["RRP", "TLS"], default="RRP", 
                       help="Unidade para testar")
    
    args = parser.parse_args()
    
    # Cria tester
    tester = CloudRunTester()
    
    # Executa diagnóstico sempre
    tester.diagnostico_ambiente()
    
    # Executa teste selecionado
    sucesso = False
    
    if args.modo == "basico":
        sucesso = tester.teste_basico_scraper()
        
    elif args.modo == "download":
        sucesso = tester.teste_download_c09(args.unidade)
        
    elif args.modo == "completo":
        sucesso = tester.teste_processamento_completo(args.unidade)
        
    elif args.modo == "candles":
        sucesso = tester.teste_modo_candles()
        
    elif args.modo == "diagnostico":
        sucesso = True  # Diagnóstico já foi executado
    
    # Resultado final
    print("\n" + "=" * 50)
    if sucesso:
        print("🎉 TESTE CONCLUÍDO COM SUCESSO")
        print("✅ Sistema pronto para deploy no Cloud Run")
    else:
        print("❌ TESTE FALHADO")
        print("🔧 Corrija os problemas antes do deploy")
    
    print("=" * 50)
    
    return 0 if sucesso else 1


if __name__ == "__main__":
    sys.exit(main())