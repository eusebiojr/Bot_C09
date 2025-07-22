# core/rafael_integration.py
"""
Módulo de integração com o código de processamento adicional (Reports + Sentinela).
Encapsula as funções do Rafael em uma classe organizadora.
"""

import os
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from io import BytesIO
from typing import Dict, Any
from openpyxl import load_workbook
from openpyxl.worksheet.table import Table, TableStyleInfo
from office365.sharepoint.client_context import ClientContext
from office365.runtime.auth.user_credential import UserCredential


class RafaelProcessor:
    """
    Processador que encapsula as funcionalidades do código do Rafael.
    Responsável por: Reports, Candles, Sistema Sentinela e Alertas SharePoint.
    """
    
    def __init__(self, unidade: str, config: Dict[str, Any]):
        """
        Inicializa processador Rafael.
        
        Args:
            unidade: Nome da unidade (RRP, TLS, etc.)
            config: Configuração completa do sistema
        """
        self.unidade = unidade
        self.config = config
        self.credenciais = config["credenciais"]
        
        # Caminhos específicos por unidade
        self.base_reports = self._obter_base_reports_path()
        self.caminho_reports = self._obter_caminho_reports()
        
        # Configurações SharePoint para alertas
        self.site_url = "https://suzano.sharepoint.com/sites/Controleoperacional"
        self.list_name = "Desvios"
        self.username = "eusebioagj@suzano.com.br"
        self.password = "290422@Cc"
    
    def _obter_base_reports_path(self) -> str:
        """Obtém caminho base dos reports por unidade."""
        # Por enquanto hardcoded, depois pode vir da configuração
        if self.unidade == "RRP":
            return r"C:\Users\tallespaiva\Suzano S A\Controle operacional - Bases de Dados\CREARE\RRP\C09\2025"
        elif self.unidade == "TLS":
            return r"C:\Users\tallespaiva\Suzano S A\Controle operacional - Bases de Dados\CREARE\TLS\C09\2025"
        else:
            # Para novas unidades
            return r"C:\Users\tallespaiva\Suzano S A\Controle operacional - Bases de Dados\CREARE\{}\C09\2025".format(self.unidade)
    
    def _obter_caminho_reports(self) -> str:
        """Obtém caminho do arquivo de reports."""
        return os.path.join(self.base_reports, "Reports", "base de dados reports.xlsx")
    
    def salvar_arquivo_local(self, buffer_dados: BytesIO, data_referencia: datetime) -> str:
        """
        Salva arquivo tratado localmente para processamento adicional.
        
        Args:
            buffer_dados: Buffer com dados tratados
            data_referencia: Data de referência
            
        Returns:
            Caminho do arquivo salvo
        """
        # Constrói caminho baseado na estrutura existente
        ano = str(data_referencia.year)
        numero_mes = data_referencia.month
        meses_pt = {
            1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
            5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
            9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
        }
        nome_pasta_mes = f"{numero_mes:02d}. {meses_pt[numero_mes]}"
        
        nome_arquivo = f"C09 01 a {data_referencia.strftime('%d.%m.%Y')}.xlsx"
        caminho_unidade = self.base_reports.replace("\\RRP\\", f"\\{self.unidade}\\")
        caminho_final = os.path.join(caminho_unidade, ano, nome_pasta_mes, nome_arquivo)
        
        # C