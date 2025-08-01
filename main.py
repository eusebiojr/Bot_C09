# SOLUÇÃO ALTERNATIVA - main.py SEM SELENIUM
"""
Sistema C09 com download simulado para Cloud Run.
Remove dependência do Selenium que está causando crashes.
"""

import sys
import os
import json
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from io import BytesIO

# Força encoding UTF-8
if os.name == 'nt':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

class C09AlternativeProcessor:
    """
    Processador C09 que funciona com dados simulados.
    Para usar enquanto não resolvermos o Selenium.
    """
    
    def __init__(self):
        print("=== SISTEMA C09 ALTERNATIVO INICIADO ===")
        print("NOTA: Usando processamento simulado sem Selenium")
        
    def gerar_dados_simulados(self, unidade: str) -> BytesIO:
        """
        Gera dados simulados para teste do sistema.
        """
        import pandas as pd
        from datetime import datetime, timedelta
        
        print(f"📊 Gerando dados simulados para {unidade}...")
        
        # Dados simulados realistas
        hoje = datetime.now()
        dados = []
        
        veiculos = [f"VE{i:03d}" for i in range(1, 21)]  # 20 veículos
        
        if unidade == "RRP":
            pois = [
                "PA AGUA CLARA", "Carregamento RRp", "Descarga Inocencia", 
                "Oficina JSL", "MONTANINI", "SELVIRIA"
            ]
        else:  # TLS
            pois = [
                "Carregamento Fabrica", "FILA DESCARGA APT", "Oficina Central JSL",
                "PA Celulose", "POSTO DE ABASTECIMENTO"
            ]
        
        # Gera 1000 registros simulados
        for i in range(1000):
            veiculo = veiculos[i % len(veiculos)]
            poi = pois[i % len(pois)]
            
            data_entrada = hoje - timedelta(hours=i//10, minutes=(i*15) % 60)
            data_saida = data_entrada + timedelta(minutes=30 + (i % 120))
            
            dados.append({
                "Veículo": veiculo,
                "Ponto de Interesse": poi,
                "Data Entrada": data_entrada,
                "Data Saída": data_saida,
                "Observações": f"Simulado {i}"
            })
        
        # Cria DataFrame
        df = pd.DataFrame(dados)
        
        # Converte para Excel em memória
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Dados')
        
        buffer.seek(0)
        print(f"✅ Dados simulados gerados: {len(df)} registros")
        
        return buffer
    
    def processar_unidade_simulada(self, unidade: str) -> bool:
        """
        Processa uma unidade com dados simulados.
        """
        try:
            print(f"\n🔄 PROCESSANDO {unidade} (SIMULADO)")
            print("=" * 50)
            
            # 1. "Download" (dados simulados)
            print("[1/4] Gerando dados simulados...")
            buffer_dados = self.gerar_dados_simulados(unidade)
            
            # 2. Processamento
            print("[2/4] Processando dados...")
            buffer_processado = self.processar_dados_simulados(buffer_dados, unidade)
            
            # 3. Upload SharePoint (simulado)
            print("[3/4] Simulando upload SharePoint...")
            sucesso_upload = self.simular_upload_sharepoint(buffer_processado, unidade)
            
            # 4. Analytics (simulado)
            print("[4/4] Processando analytics...")
            self.processar_analytics_simulado(unidade)
            
            if sucesso_upload:
                print(f"✅ {unidade} processado com sucesso (SIMULADO)")
                return True
            else:
                print(f"⚠️ {unidade} processado com avisos")
                return False
                
        except Exception as e:
            print(f"❌ Erro ao processar {unidade}: {e}")
            return False
    
    def processar_dados_simulados(self, buffer_dados: BytesIO, unidade: str) -> BytesIO:
        """
        Processa dados simulados aplicando lógica básica.
        """
        import pandas as pd
        
        # Carrega dados
        buffer_dados.seek(0)
        df = pd.read_excel(buffer_dados)
        
        print(f"Dados carregados: {len(df)} registros")
        
        # Aplica processamento básico
        df_processado = df.copy()
        df_processado["Tempo (h)"] = (df_processado["Data Saída"] - df_processado["Data Entrada"]).dt.total_seconds() / 3600
        df_processado["Grupo"] = "Simulado"
        df_processado["Observação"] = "Processamento simulado - sem Selenium"
        
        # Converte de volta para Excel
        buffer_resultado = BytesIO()
        with pd.ExcelWriter(buffer_resultado, engine='openpyxl') as writer:
            df_processado.to_excel(writer, index=False, sheet_name='Relatório')
        
        buffer_resultado.seek(0)
        print(f"Processamento concluído: {len(df_processado)} registros")
        
        return buffer_resultado
    
    def simular_upload_sharepoint(self, buffer: BytesIO, unidade: str) -> bool:
        """
        Simula upload para SharePoint.
        """
        tamanho = len(buffer.getvalue())
        print(f"📤 Upload simulado: {unidade} ({tamanho} bytes)")
        print(f"📁 Destino simulado: SharePoint/CREARE/{unidade}/C09/")
        
        # Simula sucesso
        return True
    
    def processar_analytics_simulado(self, unidade: str):
        """
        Simula processamento de analytics.
        """
        print(f"📊 Analytics simulado para {unidade}")
        print(f"   - TPV médio: 2.5h")
        print(f"   - Desvios detectados: 0")
        print(f"   - Candles atualizados: ✅")

def main():
    """
    Função principal alternativa.
    """
    try:
        processor = C09AlternativeProcessor()
        
        # Processa ambas as unidades
        unidades = ["RRP", "TLS"]
        sucessos = 0
        
        for unidade in unidades:
            if processor.processar_unidade_simulada(unidade):
                sucessos += 1
        
        print(f"\n{'='*50}")
        print(f"PROCESSAMENTO ALTERNATIVO CONCLUÍDO")
        print(f"✅ Sucessos: {sucessos}/{len(unidades)}")
        print(f"📝 Nota: Sistema funcionando com dados simulados")
        print(f"🔧 Próximo passo: Resolver problema do Selenium")
        
        return 0 if sucessos == len(unidades) else 1
        
    except Exception as e:
        print(f"\n❌ ERRO CRÍTICO: {e}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())