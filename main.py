# main.py
"""
Orquestrador principal do sistema C09.
Suporta dois modos de execução:
- CANDLES: Execução a cada 10min (só atualiza reports)
- COMPLETO: Execução a cada 1h (processamento completo + alertas)
"""

import sys
import os
import json
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from io import BytesIO

# Adiciona diretórios ao path para imports
sys.path.append(str(Path(__file__).parent))

from core.scraper import criar_scraper
from core.processor import criar_processor_rrp, criar_processor_tls
from config.settings import carregar_config, validar_configuracao, ConstantesEspecificas


class C09Orchestrator:
    """
    Orquestrador principal que coordena download, processamento e upload.
    Agora com suporte a execução contínua (CANDLES/COMPLETO).
    """
    
    def __init__(self):
        """Inicializa orquestrador com configurações."""
        print(f"=== SISTEMA C09 INICIADO - {datetime.now():%Y-%m-%d %H:%M:%S} ===")
        
        # Carrega configurações
        self.config = carregar_config()
        if not validar_configuracao(self.config):
            raise ValueError("Configuração inválida")
        
        self.credenciais = self.config["credenciais"]
        
        # Detecta modo de execução
        self.modo_execucao = self._detectar_modo_execucao()
        print(f"🔧 Modo de execução: {self.modo_execucao}")
        
        # Inicializa componentes baseado no modo
        if self.modo_execucao == "CANDLES":
            # Modo rápido - não precisa de scraper
            self.scraper = None
            print("⚡ Modo CANDLES - Processamento rápido (4h de dados)")
        else:
            # Modo completo - inicializa scraper
            self.scraper = criar_scraper(
                chrome_driver_path=self.credenciais["chrome_driver_path"],
                download_timeout=ConstantesEspecificas.DOWNLOAD_TIMEOUT
            )
            print("🔄 Modo COMPLETO - Processamento completo + alertas")
        
    def _detectar_modo_execucao(self) -> str:
        """
        Detecta modo de execução via variáveis de ambiente ou request body.
        
        Returns:
            "CANDLES" ou "COMPLETO"
        """
        # Verifica variável de ambiente (Cloud Run)
        modo_env = os.getenv("EXECUTION_MODE", "").upper()
        if modo_env in ["CANDLES", "COMPLETO"]:
            return modo_env
        
        # Verifica request body (Cloud Scheduler HTTP)
        try:
            request_body = os.getenv("REQUEST_BODY", "{}")
            data = json.loads(request_body)
            modo_request = data.get("mode", "").upper()
            if modo_request in ["CANDLES", "COMPLETO"]:
                return modo_request
        except:
            pass
        
        # Verifica argumentos da linha de comando
        if len(sys.argv) > 1:
            modo_args = sys.argv[1].upper()
            if modo_args in ["CANDLES", "COMPLETO"]:
                return modo_args
        
        # Default para desenvolvimento local
        return "COMPLETO"
        
    def _obter_periodo_execucao(self) -> tuple[datetime, datetime]:
        """
        Define período de execução baseado no modo.
        AMBOS OS MODOS usam período completo (01/mês - hoje).
        """
        hoje = datetime.now()
        
        # SEMPRE usa período completo (01 do mês até hoje)
        data_inicial = hoje.replace(day=1)
        data_final = hoje
        
        if self.modo_execucao == "CANDLES":
            print(f"Período CANDLES: {data_inicial.date()} até {data_final.date()} (completo)")
        else:
            print(f"Período COMPLETO: {data_inicial.date()} até {data_final.date()}")
        
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
    
    def processar_unidade_modo_candles(self, unidade_config: dict) -> bool:
        """
        Modo CANDLES: Download completo (01-hoje) + processamento + atualiza APENAS candles.
        NÃO executa: alertas, TPV/DM, upload arquivo principal.
        """
        unidade = unidade_config["unidade"]
        empresa_frotalog = unidade_config["empresa_frotalog"]
        
        try:
            print(f"\n⚡ CANDLES {unidade} - Download e atualização de candles")
            
            # 1. Obtém período completo (01/mês - hoje)
            data_inicial, data_final = self._obter_periodo_execucao()
            print(f"📅 Período: {data_inicial.date()} até {data_final.date()}")
            
            # 2. Download com período completo (igual ao modo COMPLETO)
            print(f"📥 Baixando relatório C09...")
            caminho_relatorio = self.scraper.baixar_relatorio_c09(
                empresa_frotalog=empresa_frotalog,
                data_inicial=data_inicial,
                data_final=data_final
            )
            
            # 3. Processamento completo dos dados
            print(f"⚙️ Processando dados...")
            processor = self._criar_processor_para_unidade(unidade)
            buffer_tratado = processor.processar_relatorio_c09(caminho_relatorio)
            
            # 4. Atualiza APENAS candles (sem alertas, sem métricas pesadas)
            print(f"📊 Atualizando candles (sem alertas)...")
            sucesso_candles = self._processar_candles_sem_alertas(
                unidade=unidade,
                buffer_tratado=buffer_tratado,
                data_referencia=data_final
            )
            
            # 5. Limpeza do arquivo temporário
            self._limpar_arquivo_temporario(caminho_relatorio)
            
            if sucesso_candles:
                print(f"✅ CANDLES {unidade} - Atualizados com sucesso")
                return True
            else:
                print(f"⚠️ CANDLES {unidade} - Falha na atualização")
                return False
                
        except Exception as e:
            print(f"❌ ERRO CANDLES {unidade}: {e}")
            self._log_erro_detalhado(e, f"Modo CANDLES - Unidade {unidade}")
            return False
    
    def _processar_candles_sem_alertas(self, unidade: str, buffer_tratado: BytesIO, 
                                    data_referencia: datetime) -> bool:
        """
        Processa apenas candles sem sistema de alertas (versão light para modo CANDLES).
        
        Args:
            unidade: Nome da unidade
            buffer_tratado: Buffer com dados processados
            data_referencia: Data de referência
            
        Returns:
            True se processamento bem-sucedido
        """
        try:
            from core.analytics_processor import criar_analytics_processor
            
            processor_analytics = criar_analytics_processor(
                unidade=unidade,
                config=self.config
            )
            
            # Carrega dados do buffer
            df = processor_analytics.carregar_planilha_buffer(buffer_tratado)
            if df.empty:
                print("⚠️ Dados vazios para candles")
                return True  # Não é erro, apenas sem dados novos
            
            print(f"📊 Processando candles com {len(df)} registros")
            
            # Define POIs para candles baseado na unidade
            if unidade == "RRP":
                pois_candles = ["Descarga Inocencia", "Carregamento Fabrica RRP", "PA AGUA CLARA", "Oficina JSL"]
            elif unidade == "TLS":
                pois_candles = ["PA Celulose", "Manutencao Celulose", "Carregamento Fabrica", "Descarga TAP", "Oficina Central JSL"]
            else:
                print(f"⚠️ Unidade {unidade} não configurada para candles")
                return False
            
            # Processa candles para cada POI
            mes_atual = data_referencia.month
            ano_atual = data_referencia.year
            
            sucessos = 0
            total_eventos = 0
            
            for poi in pois_candles:
                print(f"📈 Processando candles: {poi}")
                
                # Gera candles para este POI (já com correção de saídas falsas)
                df_eventos, df_resumo_hora = processor_analytics.gerar_candles_poi(df, poi)
                
                if not df_eventos.empty:
                    # Atualiza candles no SharePoint
                    sucesso = processor_analytics.reports_manager.atualizar_candles(
                        df_eventos_novos=df_eventos,
                        df_resumo_novos=df_resumo_hora,
                        poi=poi,
                        mes=mes_atual,
                        ano=ano_atual
                    )
                    
                    if sucesso:
                        sucessos += 1
                        total_eventos += len(df_eventos)
                        print(f"✅ {poi}: {len(df_eventos)} eventos atualizados")
                    else:
                        print(f"⚠️ {poi}: Falha na atualização SharePoint")
                else:
                    print(f"ℹ️ {poi}: Nenhum evento no período")
                    sucessos += 1  # Sem dados é normal, não é erro
            
            # Log final
            print(f"📊 RESUMO CANDLES: {sucessos}/{len(pois_candles)} POIs processados")
            print(f"📈 Total de eventos processados: {total_eventos}")
            
            # Considera sucesso se processou todos os POIs
            return sucessos == len(pois_candles)
            
        except ImportError as e:
            print(f"❌ Erro de import no processamento candles: {e}")
            return False
            
        except Exception as e:
            print(f"❌ Erro no processamento candles: {e}")
            return False

    def processar_unidade_modo_completo(self, unidade_config: dict) -> bool:
        """
        Processamento completo - download + processamento + alertas (modo 1h).
        
        Args:
            unidade_config: Configuração da unidade
            
        Returns:
            True se processamento bem-sucedido
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
            
            # 5. Processamento de analytics completo (com alertas)
            print(f"\n[4/4] Processamento de analytics...")
            self._processar_analytics(unidade, buffer_tratado, data_final)
            
            # 6. Limpeza
            self._limpar_arquivo_temporario(caminho_relatorio)
            
            print(f"✅ Unidade {unidade} processada com sucesso!")
            return True
            
        except Exception as e:
            print(f"❌ ERRO ao processar unidade {unidade}: {e}")
            self._log_erro_detalhado(e, f"Modo COMPLETO - Unidade {unidade}")
            return False
    
    def _processar_analytics_tempo_real(self, unidade: str) -> bool:
        """
        Processamento de analytics em tempo real (só candles/reports).
        
        Args:
            unidade: Nome da unidade
            
        Returns:
            True se processamento bem-sucedido
        """
        try:
            from core.analytics_processor import criar_analytics_processor
            
            processor_analytics = criar_analytics_processor(
                unidade=unidade,
                config=self.config
            )
            
            # Método específico para tempo real (implementar no analytics_processor)
            sucesso = processor_analytics.processar_tempo_real(horas_periodo=4)
            
            return sucesso
            
        except ImportError as e:
            print(f"❌ Erro de import no analytics: {e}")
            return False
            
        except Exception as e:
            print(f"❌ Erro no processamento tempo real {unidade}: {e}")
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
        Executa processamento de analytics e alertas (modo completo).
        
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
    
    def _log_erro_detalhado(self, erro: Exception, contexto: str):
        """
        Registra erro detalhado para debugging.
        
        Args:
            erro: Exception capturada
            contexto: Contexto onde ocorreu o erro
        """
        erro_detalhado = {
            "timestamp": datetime.now().isoformat(),
            "contexto": contexto,
            "erro": str(erro),
            "tipo": type(erro).__name__,
            "traceback": traceback.format_exc()
        }
        
        # Log para arquivo
        log_file = Path(__file__).parent / "logs" / "erros_detalhados.json"
        log_file.parent.mkdir(exist_ok=True)
        
        try:
            import json
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(erro_detalhado, ensure_ascii=False) + "\n")
        except:
            pass  # Se falhar o log, não quebra o sistema
    
    def executar_com_retry(self, max_tentativas: int = 10) -> bool:
        """
        Executa ciclo com sistema de retry.
        
        Args:
            max_tentativas: Máximo de tentativas em caso de falha
            
        Returns:
            True se executado com sucesso
        """
        for tentativa in range(1, max_tentativas + 1):
            try:
                if self.modo_execucao == "CANDLES":
                    sucesso = self.executar_ciclo_candles()
                else:
                    sucesso = self.executar_ciclo_completo()
                
                if sucesso:
                    return True
                else:
                    print(f"⚠️ Tentativa {tentativa}/{max_tentativas} falhou")
                    
            except Exception as e:
                print(f"❌ Tentativa {tentativa}/{max_tentativas} - Erro: {e}")
                self._log_erro_detalhado(e, f"Tentativa {tentativa}")
                
                if tentativa == max_tentativas:
                    # Última tentativa - enviar e-mail de falha crítica
                    self._notificar_falha_critica(e, tentativa)
                    return False
                
                # Aguarda antes da próxima tentativa (backoff exponencial)
                import time
                time.sleep(min(60 * tentativa, 600))  # Max 10 min
        
        return False
    
    def executar_ciclo_candles(self) -> bool:
        """
        Executa ciclo rápido para todas as unidades (modo 10min).
        
        Returns:
            True se todas as unidades processadas com sucesso
        """
        unidades_ativas = [u for u in self.config["unidades"] if u.get("ativo", True)]
        
        print(f"🔄 MODO CANDLES - Atualizando {len(unidades_ativas)} unidades...")
        
        sucessos = 0
        falhas = 0
        
        for unidade_config in unidades_ativas:
            sucesso = self.processar_unidade_modo_candles(unidade_config)
            
            if sucesso:
                sucessos += 1
            else:
                falhas += 1
        
        # Relatório resumido
        print(f"\n📊 CANDLES CONCLUÍDO: {sucessos}✅ {falhas}❌")
        return falhas == 0
    
    def executar_ciclo_completo(self) -> bool:
        """
        Executa ciclo completo para todas as unidades (modo 1h).
        
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
            
            sucesso = self.processar_unidade_modo_completo(unidade_config)
            
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
            self._notificar_falhas(falhas)
        
        return falhas == 0
    
    def _notificar_falhas(self, num_falhas: int):
        """
        Notifica falhas por e-mail.
        
        Args:
            num_falhas: Número de falhas ocorridas
        """
        try:
            from core.email_notifier import EmailNotifier
            
            notifier = EmailNotifier(self.config)
            notifier.enviar_falha_sistema(
                erro=f"{num_falhas} unidade(s) falharam no processamento",
                contexto=f"Modo {self.modo_execucao}",
                timestamp=datetime.now()
            )
        except ImportError:
            print(f"⚠️ Sistema de e-mail não implementado ainda")
        except Exception as e:
            print(f"⚠️ Falha ao enviar e-mail: {e}")
    
    def _notificar_falha_critica(self, erro: Exception, tentativas: int):
        """
        Notifica falha crítica após esgotar tentativas.
        
        Args:
            erro: Exception que causou a falha
            tentativas: Número de tentativas realizadas
        """
        try:
            from core.email_notifier import EmailNotifier
            
            notifier = EmailNotifier(self.config)
            notifier.enviar_falha_critica(
                erro=erro,
                tentativas=tentativas,
                modo=self.modo_execucao,
                timestamp=datetime.now()
            )
        except ImportError:
            print(f"⚠️ Sistema de e-mail não implementado ainda")
        except Exception as e:
            print(f"⚠️ Falha ao enviar e-mail crítico: {e}")


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
                # Executa orquestrador com retry
                orchestrator = C09Orchestrator()
                sucesso = orchestrator.executar_com_retry(max_tentativas=10)
                
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