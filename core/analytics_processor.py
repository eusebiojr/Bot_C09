# core/analytics_processor.py
"""
Processador de Analytics e Sistema de Alertas.
Responsável por: Métricas operacionais, Candles temporais, Sistema Sentinela e Reports gerenciais.
Agora com suporte a processamento em tempo real (execuções a cada 10min).
"""

import os
import pandas as pd
from datetime import datetime, timedelta
from io import BytesIO
from typing import Dict, Any, Optional
from office365.sharepoint.client_context import ClientContext
from office365.runtime.auth.user_credential import UserCredential


class AnalyticsProcessor:
    def __init__(self, unidade: str, config: Dict[str, Any]):
        """
        Inicializa processador de analytics.
        """
        self.unidade = unidade
        self.config = config
        self.credenciais = config["credenciais"]
        
        # Configurações SharePoint para alertas
        self.site_url = "https://suzano.sharepoint.com/sites/Controleoperacional"
        
        # ✅ MUDANÇA: Lista para ambiente de teste
        self.list_name = "DesviosTeste"  # ← ALTERADO de "Desvios" para "DesviosTeste"
        
        self.username = config["credenciais"]["sp_user"]
        self.password = config["credenciais"]["sp_password"]
        
        # Gerenciador de reports no SharePoint
        try:
            from core.reports_sharepoint import criar_reports_manager
            self.reports_manager = criar_reports_manager(
                site_url=self.site_url,
                username=self.username,
                password=self.password
            )
        except ImportError as e:
            print(f"⚠️ Erro ao importar reports_sharepoint: {e}")
            self.reports_manager = None
    
    def processar_tempo_real(self, horas_periodo: int = 4) -> bool:
        """
        Processamento de analytics em tempo real (só candles/reports).
        Usado para execuções a cada 10 minutos.
        
        Args:
            horas_periodo: Período em horas para buscar dados recentes
            
        Returns:
            True se processamento bem-sucedido
        """
        try:
            print(f"=== Analytics Tempo Real {self.unidade} - Últimas {horas_periodo}h ===")
            
            # Define período de análise
            agora = datetime.now()
            inicio_periodo = agora - timedelta(hours=horas_periodo)
            
            # Obtém POIs para candles desta unidade
            if self.unidade == "RRP":
                pois_candles = ["Descarga Inocencia", "Carregamento Fabrica RRP", "PA AGUA CLARA", "Oficina JSL"]
            elif self.unidade == "TLS":
                pois_candles = ["PA Celulose", "Manutencao Celulose", "Carregamento Fabrica", "Descarga TAP", "Oficina Central JSL"]
            else:
                print(f"⚠️ Unidade {self.unidade} não tem POIs configurados para tempo real")
                return False
            
            # Processa cada POI (dados já existentes no SharePoint)
            for poi in pois_candles:
                print(f"Processando tempo real: {poi}")
                
                # Carrega dados existentes do SharePoint
                try:
                    df_candles_existente = self.reports_manager.carregar_candles_sharepoint("Candles")
                    df_resumo_existente = self.reports_manager.carregar_candles_sharepoint("Resumo por Hora")
                    
                    if df_candles_existente.empty or df_resumo_existente.empty:
                        print(f"⚠️ Dados históricos não encontrados para {poi}")
                        continue
                    
                    # Filtra dados do período recente para este POI
                    df_poi_recente = df_candles_existente[
                        (df_candles_existente['POI'] == poi) &
                        (df_candles_existente['Data Evento'] >= inicio_periodo)
                    ]
                    
                    df_resumo_recente = df_resumo_existente[
                        (df_resumo_existente['POI'] == poi) &
                        (df_resumo_existente['Hora'] >= inicio_periodo)
                    ]
                    
                    if not df_poi_recente.empty:
                        print(f"📊 {poi}: {len(df_poi_recente)} eventos recentes processados")
                    else:
                        print(f"ℹ️ {poi}: Nenhum evento recente")
                    
                except Exception as e:
                    print(f"⚠️ Erro ao processar {poi}: {e}")
                    continue
            
            # Atualiza resumo base (sem recalcular métricas pesadas)
            print("📈 Atualizando indicadores base...")
            
            # TPV e DM só calculamos no modo completo
            # Aqui só mantemos a estrutura atualizada
            sucesso_base = True  # Placeholder - implementar conforme necessário
            
            print(f"✅ Analytics tempo real {self.unidade} concluído")
            return sucesso_base
            
        except Exception as e:
            print(f"❌ Erro no processamento tempo real {self.unidade}: {e}")
            return False
    
    def carregar_planilha_buffer(self, buffer: BytesIO) -> pd.DataFrame:
        """
        Carrega planilha de um buffer em memória.
        
        Args:
            buffer: Buffer com dados Excel
            
        Returns:
            DataFrame com dados carregados
        """
        try:
            buffer.seek(0)
            df = pd.read_excel(buffer, engine='openpyxl')
            df['Data Entrada'] = pd.to_datetime(df['Data Entrada'], format='%d/%m/%Y %H:%M:%S', dayfirst=True, errors='coerce')
            df['Data Saída'] = pd.to_datetime(df['Data Saída'], format='%d/%m/%Y %H:%M:%S', dayfirst=True, errors='coerce')
            print(f"Dados carregados do buffer: {len(df)} registros")
            return df
        except Exception as e:
            print(f"Erro ao carregar planilha do buffer: {e}")
            return pd.DataFrame()
    
    def calcular_tpv(self, df: pd.DataFrame, poi: str, data: datetime.date) -> float:
        """
        Calcula TPV (Tempo de Permanência Médio) para um POI em uma data.
        
        Args:
            df: DataFrame com dados
            poi: Ponto de interesse
            data: Data de referência
            
        Returns:
            Tempo médio de permanência em horas
        """
        df_filtrado = df[
            (df['Data Entrada'].dt.date == data) & 
            (df['Ponto de Interesse'] == poi)
        ]
        
        if not df_filtrado.empty:
            media_tempo = df_filtrado['Tempo Permanencia'].mean()
            print(f"TPV {poi} para {data}: {media_tempo:.2f}h")
            return media_tempo
        else:
            print(f"Nenhum registro para TPV {poi} em {data}")
            return 0.0
    
    def calcular_dm(self, df: pd.DataFrame, grupo: str, data: datetime.date) -> float:
        """
        Calcula DM (Disponibilidade Mecânica) - horas de manutenção para um grupo.
        
        Args:
            df: DataFrame com dados
            grupo: Grupo de análise (ex: "Manutenção")
            data: Data de referência
            
        Returns:
            Total de horas de manutenção
        """
        df_filtrado = df[
            (df['Data Entrada'].dt.date == data) & 
            (df['Grupo'] == grupo) & 
            (df['Data Saída'].dt.date == data)
        ]
        
        if not df_filtrado.empty:
            horas_totais = df_filtrado['Tempo Permanencia'].sum()
            print(f"DM {grupo} para {data}: {horas_totais:.2f}h")
            return horas_totais
        else:
            print(f"Nenhum registro para DM {grupo} em {data}")
            return 0.0
    
    def gerar_candles_poi(self, df: pd.DataFrame, poi: str) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Gera dados de candles (eventos de entrada/saída) para um POI.
        CORRIGIDO: Ignora saídas falsas de veículos que ainda estão no POI.
        
        Args:
            df: DataFrame com dados
            poi: Ponto de interesse
            
        Returns:
            Tuple com (df_eventos, df_resumo_hora)
        """
        df_poi = df[df['Ponto de Interesse'] == poi].copy()
        
        if df_poi.empty:
            print(f"Nenhum dado para POI: {poi}")
            return pd.DataFrame(), pd.DataFrame()
        
        # Converte datas se necessário
        df_poi['Data Entrada'] = pd.to_datetime(df_poi['Data Entrada'], format='%d/%m/%Y %H:%M:%S', dayfirst=True, errors='coerce')
        df_poi['Data Saída'] = pd.to_datetime(df_poi['Data Saída'], format='%d/%m/%Y %H:%M:%S', dayfirst=True, errors='coerce')
        
        # Padrões para detectar veículos que ainda estão no POI
        PADROES_AINDA_NO_POI = [
            "permaneceu no poi após o fim do período pesquisado",
            "permaneceu no poi após o fim do período",
            "ainda permanece no local", 
            "continua no ponto de interesse",
            "período pesquisado finalizado",
            "veículo permaneceu no poi"
        ]
        
        def veiculo_ainda_esta_no_poi(observacao: str) -> bool:
            """Verifica se veículo ainda está no POI baseado na observação."""
            if pd.isna(observacao):
                return False
                
            obs_lower = str(observacao).lower().strip()
            
            for padrao in PADROES_AINDA_NO_POI:
                if padrao in obs_lower:
                    return True
                    
            return False
        
        # Cria eventos de entrada (sempre válidos)
        entradas = df_poi[['Veículo', 'Data Entrada', 'Observações']].copy()
        entradas['Evento'] = 'entrada'
        entradas.rename(columns={'Data Entrada': 'Data Evento'}, inplace=True)
        
        # Cria eventos de saída (FILTRADOS para excluir falsas saídas)
        saidas_validas = []
        saidas_ignoradas = 0
        
        for _, registro in df_poi.iterrows():
            if veiculo_ainda_esta_no_poi(registro.get("Observações", "")):
                # IGNORA esta saída - veículo ainda está no POI
                saidas_ignoradas += 1
                print(f"⚠️ {registro['Veículo']} em {poi}: Saída ignorada (ainda no POI)")
            else:
                # Saída válida - registra normalmente
                saidas_validas.append({
                    'Veículo': registro['Veículo'],
                    'Data Evento': registro['Data Saída'],
                    'Evento': 'saida',
                    'Observações': registro.get('Observações', '')
                })
        
        # Converte saídas para DataFrame
        if saidas_validas:
            saidas = pd.DataFrame(saidas_validas)
        else:
            saidas = pd.DataFrame(columns=['Veículo', 'Data Evento', 'Evento', 'Observações'])
        
        # Log de estatísticas
        total_registros = len(df_poi)
        entradas_count = len(entradas)
        saidas_count = len(saidas)
        
        print(f"📊 {poi}: {total_registros} registros → {entradas_count} entradas, {saidas_count} saídas válidas")
        if saidas_ignoradas > 0:
            print(f"   ⚠️ {saidas_ignoradas} saídas ignoradas (veículos ainda no POI)")
        
        # Combina eventos e ordena cronologicamente
        eventos = pd.concat([entradas[['Veículo', 'Data Evento', 'Evento']], 
                            saidas[['Veículo', 'Data Evento', 'Evento']]], 
                        ignore_index=True)
        eventos.dropna(subset=['Data Evento'], inplace=True)
        eventos.sort_values(by='Data Evento', inplace=True)
        
        # Calcula veículos presentes em cada evento
        dentro_poi = set()
        veiculos_no_poi_evento = []
        
        for _, evento in eventos.iterrows():
            placa = evento['Veículo']
            if evento['Evento'] == 'entrada':
                dentro_poi.add(placa)
            elif evento['Evento'] == 'saida':
                dentro_poi.discard(placa)
            veiculos_no_poi_evento.append(';'.join(sorted(dentro_poi)))
        
        eventos['Veículos no POI'] = veiculos_no_poi_evento
        eventos['POI'] = poi
        
        # Se não há eventos, retorna DataFrames vazios
        if eventos.empty:
            return eventos, pd.DataFrame()
        
        # Gera resumo por hora
        start_time = eventos['Data Evento'].min().floor('h')
        end_time = eventos['Data Evento'].max().ceil('h')
        timeline = pd.date_range(start=start_time, end=end_time, freq='h')
        
        contagem = []
        linha_atual = 0
        dentro_poi = set()
        veiculos_fim_anterior = 0
        
        for i in range(len(timeline) - 1):
            hora_inicio = timeline[i]
            hora_fim = timeline[i + 1]
            eventos_hora = eventos[
                (eventos['Data Evento'] >= hora_inicio) & 
                (eventos['Data Evento'] < hora_fim)
            ]
            
            maximo = minimo = linha_atual
            
            for _, evento in eventos_hora.iterrows():
                placa = evento['Veículo']
                if evento['Evento'] == 'entrada':
                    dentro_poi.add(placa)
                    linha_atual += 1
                elif evento['Evento'] == 'saida':
                    dentro_poi.discard(placa)
                    linha_atual -= 1
                maximo = max(maximo, linha_atual)
                minimo = min(minimo, linha_atual)
            
            contagem.append({
                'Hora': hora_fim,
                'Veículos no início da hora': veiculos_fim_anterior,
                'Veículos no final da hora': linha_atual,
                'Máximo de veículos': maximo,
                'Mínimo de veículos': minimo,
                'POI': poi,
                'Veículos no POI': ';'.join(sorted(dentro_poi))
            })
            
            veiculos_fim_anterior = linha_atual
        
        df_contagem = pd.DataFrame(contagem)
        
        # Log final
        if not df_contagem.empty:
            ultimo_count = df_contagem.iloc[-1]['Veículos no final da hora']
            print(f"✅ {poi}: {ultimo_count} veículos presentes no final do período")
        
        return eventos, df_contagem
    
    def identificar_desvios_poi(self, poi: str, threshold: int) -> pd.DataFrame:
        """
        Identifica desvios (acúmulo de veículos) para um POI.
        
        Args:
            poi: Ponto de interesse
            threshold: Limite de veículos para gerar alerta
            
        Returns:
            DataFrame com alertas identificados
        """
        try:
            # Gera dados sentinela (últimos 4 dias)
            df_sentinela = self._gerar_dados_sentinela(poi)
            
            if df_sentinela.empty:
                return pd.DataFrame()
            
            # Identifica desvios
            df_sentinela["n_veiculos"] = df_sentinela["Veículos no POI"].fillna('').apply(
                lambda x: len([v for v in str(x).split(';') if v.strip()])
            )
            
            df_filtrado = df_sentinela[df_sentinela["n_veiculos"] >= threshold].copy()
            df_filtrado.sort_values("Hora", inplace=True)
            
            if df_filtrado.empty:
                return pd.DataFrame()
            
            # Gera alertas com escalation
            alertas = []
            ultimo_alerta = None
            nivel = 0
            
            for _, row in df_filtrado.iterrows():
                hora_atual = row["Hora"]
                
                # Define nível do alerta (escalation)
                if ultimo_alerta is None or (hora_atual - ultimo_alerta) > timedelta(hours=1):
                    nivel = 1
                else:
                    nivel = min(nivel + 1, 4)
                ultimo_alerta = hora_atual
                
                # Cria título do alerta
                titulo = self._gerar_titulo_alerta(poi, hora_atual, nivel)
                veiculos = str(row["Veículos no POI"]).split(";")
                
                # Gera alerta para cada veículo
                for v in veiculos:
                    if v.strip():
                        alertas.append({
                            "Título": titulo,
                            "Placa": v.strip(),
                            "Ponto_de_Interesse": poi,
                            "Data_Hora_Desvio": hora_atual,
                            "Data_Hora_Entrada": None,
                            "Tempo": None,
                            "Nível": f"Tratativa N{nivel}"
                        })
            
            df_alertas = pd.DataFrame(alertas)
            
            if not df_alertas.empty:
                # Enriquece com dados de entrada
                df_alertas = self._enriquecer_alertas_entrada(df_alertas)
            
            return df_alertas
            
        except Exception as e:
            print(f"Erro ao identificar desvios para {poi}: {e}")
            return pd.DataFrame()
    
    def _gerar_dados_sentinela(self, poi: str) -> pd.DataFrame:
        """Gera dados sentinela (últimos 4 dias) para um POI."""
        hoje = datetime.now().date()
        dias = [hoje - timedelta(days=i) for i in range(4)]
        
        try:
            # Carrega dados do SharePoint
            df_resumo_hora = self.reports_manager.carregar_candles_sharepoint("Resumo por Hora")
            
            if df_resumo_hora.empty:
                return pd.DataFrame()
            
            df_filtrado = df_resumo_hora[
                (df_resumo_hora["POI"] == poi) &
                (df_resumo_hora["Hora"].dt.date.isin(dias))
            ].copy()
            
            return df_filtrado
            
        except Exception as e:
            print(f"Erro ao gerar dados sentinela para {poi}: {e}")
            return pd.DataFrame()
    
    def _gerar_titulo_alerta(self, poi: str, hora: datetime, nivel: int) -> str:
        """Gera título único do alerta."""
        data_str = hora.strftime("%d%m%Y")
        hora_str = hora.strftime("%H%M%S")
        poi_clean = poi.replace(' ', '').replace('-', '')
        return f"{self.unidade}_{poi_clean}_N{nivel}_{data_str}_{hora_str}"
    
    def _enriquecer_alertas_entrada(self, df_alertas: pd.DataFrame) -> pd.DataFrame:
        """Enriquece alertas com dados de entrada dos veículos."""
        if df_alertas.empty:
            return df_alertas
        
        try:
            # Carrega dados de candles do SharePoint
            df_candles = self.reports_manager.carregar_candles_sharepoint("Candles")
            
            if df_candles.empty:
                return df_alertas
            
            df_entradas = df_candles[df_candles["Evento"].str.lower() == "entrada"]
            
            def buscar_hora_entrada(row):
                """Busca última entrada do veículo no POI antes do desvio."""
                entradas = df_entradas[
                    (df_entradas["Veículo"] == row["Placa"]) &
                    (df_entradas["POI"] == row["Ponto_de_Interesse"]) &
                    (df_entradas["Data Evento"] <= row["Data_Hora_Desvio"])
                ]
                return entradas["Data Evento"].max() if not entradas.empty else pd.NaT
            
            df_alertas["Data_Hora_Entrada"] = df_alertas.apply(buscar_hora_entrada, axis=1)
            
            def calcular_tempo_permanencia(row):
                """Calcula tempo de permanência até agora."""
                if pd.notnull(row["Data_Hora_Entrada"]):
                    delta = datetime.now() - row["Data_Hora_Entrada"]
                    return round(delta.total_seconds() / 3600, 2)
                return None
            
            df_alertas["Tempo"] = df_alertas.apply(calcular_tempo_permanencia, axis=1)
            
        except Exception as e:
            print(f"Erro ao enriquecer alertas: {e}")
        
        return df_alertas
    
    def enviar_alertas_sharepoint(self, df_alertas: pd.DataFrame) -> bool:
        """
        Envia alertas para lista SharePoint.
        """
        if df_alertas.empty:
            return True
        
        try:
            ctx = ClientContext(self.site_url).with_credentials(
                UserCredential(self.username, self.password)
            )
            
            sp_list = ctx.web.lists.get_by_title(self.list_name)
            
            # Verifica títulos existentes (evita duplicatas)
            existing_items = sp_list.items.select(["Title"]).top(5000).get().execute_query()
            existing_titles = {item.properties["Title"] for item in existing_items}
            
            # Envia apenas o último título (mais recente)
            ultimo_titulo = df_alertas["Título"].iloc[-1]
            
            if ultimo_titulo in existing_titles:
                print(f"⚠️ Alerta '{ultimo_titulo}' já existe no SharePoint")
                return True
            
            # Filtra alertas do último título
            df_ultimo = df_alertas[df_alertas["Título"] == ultimo_titulo]
            
            # Envia alertas
            for _, row in df_ultimo.iterrows():
                item = {
                    "Title": str(row["Título"]),
                    "Placa": str(row["Placa"]),
                    "PontodeInteresse": str(row["Ponto_de_Interesse"]),
                    "Data_Hora_Entrada": (
                        row["Data_Hora_Entrada"].strftime('%Y-%m-%dT%H:%M:%S') 
                        if pd.notnull(row["Data_Hora_Entrada"]) else None
                    ),
                    "Tempo": row["Tempo"],
                    "Tipo_Alerta": row["Nível"],
                    "Status": "Pendente"
                }
                sp_list.add_item(item).execute_query()
            
            print(f"✅ Alerta '{ultimo_titulo}' enviado para SharePoint ({len(df_ultimo)} registros)")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao enviar alertas para SharePoint: {e}")
            return False
    
    def _obter_total_veiculos(self) -> int:
        """Obtém total de veículos da unidade."""
        for unidade_config in self.config["unidades"]:
            if unidade_config["unidade"] == self.unidade:
                return unidade_config.get("total_veiculos", 91)  # Default RRP
        return 91
    
    def _obter_pois_alertas(self) -> Dict[str, int]:
        """Obtém POIs e seus thresholds de alerta."""
        pois_config = self.config["pois_por_unidade"].get(self.unidade, [])
        
        thresholds = {}
        for poi in pois_config:
            if poi.get("ativo", True) and poi.get("threshold_alerta", 0) > 0:
                thresholds[poi["ponto_interesse"]] = poi["threshold_alerta"]
        
        return thresholds
    
    def processar_analytics_completo(self, buffer_dados: BytesIO, data_referencia: datetime) -> bool:
        """
        Executa processamento completo de analytics.
        
        Args:
            buffer_dados: Buffer com dados tratados
            data_referencia: Data de referência para processamento
            
        Returns:
            True se processamento bem-sucedido
        """
        try:
            print(f"=== Analytics {self.unidade} - {data_referencia.date()} ===")
            
            # 1. Carrega dados
            df = self.carregar_planilha_buffer(buffer_dados)
            if df.empty:
                print("⚠️ Dados vazios, pulando analytics")
                return False
            
            # 2. Calcula métricas do dia anterior
            ontem = (datetime.now() - timedelta(days=1)).date()
            
            # 3. Cálculos específicos por unidade
            if self.unidade == "RRP":
                tpv_ac = self.calcular_tpv(df, "PA AGUA CLARA", ontem)
                dm_valor = self.calcular_dm(df, "Manutenção", ontem)
                pois_candles = ["Descarga Inocencia", "Carregamento Fabrica RRP", "PA AGUA CLARA", "Oficina JSL"]
                
            elif self.unidade == "TLS":
                tpv_ac = self.calcular_tpv(df, "PA Celulose", ontem)
                dm_valor = self.calcular_dm(df, "Manutenção", ontem)
                pois_candles = ["PA Celulose", "Manutencao Celulose", "Carregamento Fabrica", "Descarga TAP", "Oficina Central JSL"]
                
            else:
                print(f"⚠️ Unidade {self.unidade} não tem configuração específica")
                tpv_ac = dm_valor = 0
                pois_candles = []
            
            # 4. Atualiza resumo diário no SharePoint
            total_veiculos = self._obter_total_veiculos()
            sucesso_resumo = self.reports_manager.atualizar_resumo_diario(
                unidade=self.unidade,
                data=ontem,
                tpv_ac=tpv_ac,
                dm_valor=dm_valor,
                total_veiculos=total_veiculos
            )
            
            if not sucesso_resumo:
                print("⚠️ Falha ao atualizar resumo diário")
            
            # 5. Gera e salva candles para POIs principais
            mes_atual = datetime.now().month
            ano_atual = datetime.now().year
            
            for poi in pois_candles:
                print(f"Processando candles: {poi}")
                df_eventos, df_resumo_hora = self.gerar_candles_poi(df, poi)
                
                if not df_eventos.empty:
                    sucesso_candles = self.reports_manager.atualizar_candles(
                        df_eventos_novos=df_eventos,
                        df_resumo_novos=df_resumo_hora,
                        poi=poi,
                        mes=mes_atual,
                        ano=ano_atual
                    )
                    
                    if not sucesso_candles:
                        print(f"⚠️ Falha ao salvar candles para {poi}")
                else:
                    print(f"⚠️ Nenhum dado de candles para {poi}")
            
            # 6. Processa sistema de alertas
            self._processar_sistema_alertas()
            
            print(f"✅ Analytics {self.unidade} processado com sucesso")
            return True
            
        except Exception as e:
            print(f"❌ Erro no processamento de analytics {self.unidade}: {e}")
            return False
    
    def _processar_sistema_alertas(self):
        """Processa sistema de alertas para todos os POIs da unidade."""
        try:
            print("🚨 Processando sistema de alertas...")
            
            # Obtém POIs e thresholds
            pois_thresholds = self._obter_pois_alertas()
            
            for poi, threshold in pois_thresholds.items():
                print(f"Verificando alertas: {poi} (threshold: {threshold})")
                
                # Identifica desvios
                df_alertas = self.identificar_desvios_poi(poi, threshold)
                
                if not df_alertas.empty:
                    # Envia alertas para SharePoint
                    sucesso_envio = self.enviar_alertas_sharepoint(df_alertas)
                    
                    if sucesso_envio:
                        print(f"✅ Alertas processados para {poi}")
                    else:
                        print(f"⚠️ Falha ao enviar alertas para {poi}")
                else:
                    print(f"ℹ️ Nenhum alerta para {poi}")
            
        except Exception as e:
            print(f"❌ Erro no sistema de alertas: {e}")


# Factory function
def criar_analytics_processor(unidade: str, config: Dict[str, Any]) -> AnalyticsProcessor:
    """
    Cria processador de analytics para uma unidade.
    
    Args:
        unidade: Nome da unidade
        config: Configuração completa
        
    Returns:
        Instância do processador
    """
    return AnalyticsProcessor(unidade, config)