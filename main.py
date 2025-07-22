# main.py
"""
Orquestrador principal do sistema C09.
Substitui C09_unificado.py com arquitetura modular e configurável.
"""

import sys
import os
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from io import BytesIO  # ← Adiciona import do BytesIO

# Adiciona diretórios ao path para imports
sys.path.append(str(Path(__file__).parent))

from core.scraper import criar_scraper
from core.processor import criar_processor_rrp, criar_processor_tls
from config.settings import carregar_config, validar_configuracao, ConstantesEspecificas


class C09Orchestrator:
    """
    Orquestrador principal que coordena download, processamento e upload.
    """
    
    def __init__(self):
        """Inicializa orquestrador com configurações."""
        print(f"=== SISTEMA C09 INICIADO - {datetime.now():%Y-%m-%d %H:%M:%S} ===")
        
        # Carrega configurações
        self.config = carregar_config()
        if not validar_configuracao(self.config):
            raise ValueError("Configuração inválida")
        
        self.credenciais = self.config["credenciais"]
        
        # Inicializa componentes
        self.scraper = criar_scraper(
            chrome_driver_path=self.credenciais["chrome_driver_path"],
            download_timeout=ConstantesEspecificas.DOWNLOAD_TIMEOUT
        )
        
    def _obter_periodo_execucao(self) -> tuple[datetime, datetime]:
        """
        Define período de execução (1º dia do mês até hoje).
        
        Returns:
            Tuple com (data_inicial, data_final)
        """
        hoje = datetime.today()
        data_inicial = hoje.replace(day=1)
        data_final = hoje
        
        print(f"Período de execução: {data_inicial.date()} até {data_final.date()}")
        return data_inicial, data_final
        
    def _criar_processor_para_unidade(self, unidade: str):
        """
        Cria processador específico para a unidade.
        
        Args:
            unidade: Nome da unidade ("RRP", "TLS", etc.)
            
        Returns:
            Processador configurado para a unidade
        """
        config_pois = self.config["pois_por_unidade"][unidade]
        
        if unidade == "RRP":
            return criar_processor_rrp(config_pois)
        elif unidade == "TLS":
            return criar_processor_tls(config_pois)
        else:
            # Para novas unidades, usar processador genérico
            from core.processor import C09DataProcessor
            return C09DataProcessor(config_pois)
    
    def processar_unidade(self, unidade_config: dict) -> bool:
        """
        Processa uma unidade completa.
        
        Args:
            unidade_config: Configuração da unidade
            
        Returns:
            True se processamento bem-sucedido, False caso contrário
        """
        unidade = unidade_config["unidade"]
        empresa_frotalog = unidade_config["empresa_frotalog"]
        
        try:
            print(f"\n{'='*60}")
            print(f"PROCESSANDO UNIDADE: {unidade}")
            print(f"Empresa Frotalog: {empresa_frotalog}")
            print(f"{'='*60}")
            
            # 1. Obtém período
            data_inicial, data_final = self._obter_periodo_execucao()
            
            # 2. Download do relatório
            print(f"\n[1/4] Baixando relatório C09...")
            caminho_relatorio = self.scraper.baixar_relatorio_c09(
                empresa_frotalog=empresa_frotalog,
                data_inicial=data_inicial,
                data_final=data_final
            )
            
            # 3. Processamento dos dados
            print(f"\n[2/4] Processando dados...")
            processor = self._criar_processor_para_unidade(unidade)
            buffer_tratado = processor.processar_relatorio_c09(caminho_relatorio)
            
            # 4. Upload para SharePoint
            print(f"\n[3/4] Enviando para SharePoint...")
            sucesso_upload = self._upload_sharepoint(
                unidade_config=unidade_config,
                data_referencia=data_final,
                buffer_tratado=buffer_tratado,
                caminho_original=caminho_relatorio
            )
            
            if not sucesso_upload:
                print(f"❌ Falha no upload para {unidade}")
                return False
            
            # 5. Processamento de analytics (Reports + Sentinela)
            print(f"\n[4/4] Processamento de analytics...")
            self._processar_analytics(unidade, buffer_tratado, data_final)
            
            # 6. Limpeza
            self._limpar_arquivo_temporario(caminho_relatorio)
            
            print(f"✅ Unidade {unidade} processada com sucesso!")
            return True
            
        except Exception as e:
            print(f"❌ ERRO ao processar unidade {unidade}: {e}")
            traceback.print_exc()
            return False
    
    def _upload_sharepoint(self, unidade_config: dict, data_referencia: datetime, 
                          buffer_tratado: BytesIO, caminho_original: str) -> bool:
        """
        Faz upload dos arquivos para SharePoint.
        
        Args:
            unidade_config: Configuração da unidade
            data_referencia: Data de referência para nome do arquivo
            buffer_tratado: Buffer com Excel tratado
            caminho_original: Caminho do arquivo original
            
        Returns:
            True se sucesso, False caso contrário
        """
        try:
            from core.sharepoint_uploader import SharePointUploader
            
            uploader = SharePointUploader(
                site_url=ConstantesEspecificas.SHAREPOINT_BASE_URL,
                username=self.credenciais["sp_user"],
                password=self.credenciais["sp_password"]
            )
            
            # Prepara dados para upload
            data_str = data_referencia.strftime("%d.%m.%Y")
            nome_arquivo = f"C09 01 a {data_str}.xlsx"
            
            numero_mes = data_referencia.month
            nome_pasta_mes = f"{numero_mes:02d}. {ConstantesEspecificas.MESES_PT[numero_mes]}"
            ano_referencia = str(data_referencia.year)
            
            # Upload arquivo tratado
            sucesso_tratado = uploader.upload_arquivo(
                base_sharepoint=unidade_config["base_sharepoint"],
                ano=ano_referencia,
                mes=nome_pasta_mes,
                nome_arquivo=nome_arquivo,
                conteudo=buffer_tratado.read(),
                is_buffer=True
            )
            
            if not sucesso_tratado:
                return False
            
            # Upload arquivo original (se configurado)
            base_original = unidade_config["base_sharepoint"] + " Original"
            sucesso_original = uploader.upload_arquivo(
                base_sharepoint=base_original,
                ano=ano_referencia,
                mes=nome_pasta_mes,
                nome_arquivo=nome_arquivo,
                conteudo=caminho_original,
                is_buffer=False
            )
            
            return sucesso_tratado and sucesso_original
            
        except ImportError as e:
            print(f"❌ Erro de import no upload SharePoint: {e}")
            print("🔧 Verifique se todos os módulos estão criados")
            return False
            
        except Exception as e:
            print(f"Erro no upload SharePoint: {e}")
            return False
    
    def _processar_analytics(self, unidade: str, buffer_tratado: BytesIO, data_referencia: datetime):
        """
        Executa processamento de analytics e alertas.
        
        Args:
            unidade: Nome da unidade
            buffer_tratado: Buffer com dados tratados
            data_referencia: Data de referência
        """
        try:
            print(f"Processando analytics para {unidade}...")
            
            from core.analytics_processor import criar_analytics_processor
            
            processor_analytics = criar_analytics_processor(
                unidade=unidade,
                config=self.config
            )
            
            sucesso = processor_analytics.processar_analytics_completo(
                buffer_dados=buffer_tratado,
                data_referencia=data_referencia
            )
            
            if not sucesso:
                print(f"⚠️ Analytics {unidade} processado com falhas")
            
        except ImportError as e:
            print(f"❌ Erro de import no analytics: {e}")
            print("🔧 Verifique se todos os módulos estão criados")
            
        except Exception as e:
            print(f"❌ Erro no processamento de analytics {unidade}: {e}")
            # Não falha o processo principal se houver erro aqui
    
    def _limpar_arquivo_temporario(self, caminho_arquivo: str):
        """Remove arquivo temporário."""
        try:
            if os.path.exists(caminho_arquivo):
                os.remove(caminho_arquivo)
                print(f"Arquivo temporário removido: {Path(caminho_arquivo).name}")
        except Exception as e:
            print(f"Aviso: Não foi possível remover arquivo temporário: {e}")
    
    def executar_ciclo_completo(self) -> bool:
        """
        Executa ciclo completo para todas as unidades ativas.
        
        Returns:
            True se todas as unidades processadas com sucesso
        """
        unidades_ativas = [u for u in self.config["unidades"] if u.get("ativo", True)]
        
        print(f"Iniciando processamento de {len(unidades_ativas)} unidades...")
        
        sucessos = 0
        falhas = 0
        
        for unidade_config in unidades_ativas:
            unidade = unidade_config["unidade"]
            print(f"\n🔄 AGUARDANDO PROCESSAMENTO DE {unidade}...")
            print(f"⏳ Outras unidades aguardarão {unidade} terminar completamente")
            
            sucesso = self.processar_unidade(unidade_config)
            
            if sucesso:
                sucessos += 1
                print(f"✅ {unidade} CONCLUÍDA - Próxima unidade pode iniciar")
            else:
                falhas += 1
                print(f"❌ {unidade} FALHADA - Continuando para próxima unidade")
            
            # Pausa entre unidades para garantir limpeza
            import time
            time.sleep(2)
        
        # Relatório final
        print(f"\n{'='*60}")
        print(f"RELATÓRIO FINAL")
        print(f"{'='*60}")
        print(f"✅ Sucessos: {sucessos}")
        print(f"❌ Falhas: {falhas}")
        print(f"📊 Total: {len(unidades_ativas)}")
        
        if falhas > 0:
            print(f"\n⚠️ ATENÇÃO: {falhas} unidade(s) falharam!")
            # Aqui seria chamado o sistema de e-mail de falha
            self._notificar_falhas(falhas)
        
        return falhas == 0
    
    def _notificar_falhas(self, num_falhas: int):
        """
        Notifica falhas por e-mail (implementar depois).
        
        Args:
            num_falhas: Número de falhas ocorridas
        """
        # TODO: Implementar notificação por e-mail
        print(f"TODO: Enviar e-mail de falha do sistema ({num_falhas} falhas)")


def main():
    """Função principal - ponto de entrada do sistema."""
    
    # Configurar logging para arquivo
    log_file = Path(__file__).parent / "logs" / "execucao.log"
    log_file.parent.mkdir(exist_ok=True)
    
    try:
        # Redireciona stdout e stderr para arquivo de log
        with open(log_file, "a", encoding="utf-8") as f:
            # Mantém saída no console também
            import sys
            
            class TeeOutput:
                def __init__(self, file, console):
                    self.file = file
                    self.console = console
                
                def write(self, data):
                    self.console.write(data)
                    self.file.write(data)
                    self.file.flush()
                
                def flush(self):
                    self.console.flush()
                    self.file.flush()
            
            # Escreve cabeçalho no log
            f.write(f"\n{'='*80}\n")
            f.write(f"EXECUÇÃO C09 - {datetime.now():%Y-%m-%d %H:%M:%S}\n")
            f.write(f"{'='*80}\n")
            f.flush()
            
            original_stdout = sys.stdout
            original_stderr = sys.stderr
            
            sys.stdout = TeeOutput(f, original_stdout)
            sys.stderr = TeeOutput(f, original_stderr)
            
            try:
                # Executa orquestrador
                orchestrator = C09Orchestrator()
                sucesso = orchestrator.executar_ciclo_completo()
                
                if sucesso:
                    print(f"\n🎉 EXECUÇÃO CONCLUÍDA COM SUCESSO - {datetime.now():%H:%M:%S}")
                    sys.exit(0)
                else:
                    print(f"\n💥 EXECUÇÃO FINALIZADA COM FALHAS - {datetime.now():%H:%M:%S}")
                    sys.exit(1)
                    
            finally:
                # Restaura stdout/stderr originais
                sys.stdout = original_stdout
                sys.stderr = original_stderr
                
    except Exception as e:
        print(f"\n💥 ERRO CRÍTICO: {e}")
        traceback.print_exc()
        
        # Escreve erro no log também
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"\n💥 ERRO CRÍTICO: {e}\n")
            traceback.print_exc(file=f)
        
        sys.exit(1)


if __name__ == "__main__":
    main()