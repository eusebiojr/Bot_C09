# config/settings.py
"""
Módulo de carregamento e validação de configurações.
Carrega configurações das planilhas Excel e variáveis de ambiente.
"""

import os
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv


class ConfigurationLoader:
    """
    Carregador de configurações do sistema C09.
    Lê planilhas Excel e variáveis de ambiente.
    """
    
    def __init__(self, config_path: str = None):
        """
        Inicializa carregador de configurações.
        
        Args:
            config_path: Caminho para arquivo unidades.xlsx. Se None, busca na pasta config/
        """
        if config_path is None:
            config_path = Path(__file__).parent / "unidades.xlsx"
        
        self.config_path = Path(config_path)
        self._validar_arquivo_config()
        
        # Carrega variáveis de ambiente
        load_dotenv()
        
    def _validar_arquivo_config(self) -> None:
        """Valida se arquivo de configuração existe."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Arquivo de configuração não encontrado: {self.config_path}")
    
    def carregar_unidades(self) -> List[Dict[str, Any]]:
        """
        Carrega configurações das unidades.
        
        Returns:
            Lista de dicionários com configuração de cada unidade
        """
        try:
            df_unidades = pd.read_excel(self.config_path, sheet_name="Unidades", engine="openpyxl")
            
            unidades = []
            for _, row in df_unidades.iterrows():
                unidade = {
                    "unidade": row["unidade"],
                    "empresa_frotalog": row["empresa_frotalog"],
                    "base_sharepoint": row["base_sharepoint"],
                    "total_veiculos": row.get("total_veiculos", 0),
                    "ativo": row.get("ativo", True)
                }
                unidades.append(unidade)
            
            # Filtra apenas unidades ativas
            unidades_ativas = [u for u in unidades if u["ativo"]]
            
            print(f"Configurações carregadas: {len(unidades_ativas)} unidades ativas")
            return unidades_ativas
            
        except Exception as e:
            print(f"Erro ao carregar configurações de unidades: {e}")
            raise
    
    def carregar_pois_unidade(self, unidade: str) -> List[Dict[str, Any]]:
        """
        Carrega configuração de POIs para uma unidade específica.
        
        Args:
            unidade: Nome da unidade (ex: "RRP", "TLS")
            
        Returns:
            Lista de dicionários com configuração dos POIs
        """
        sheet_name = f"POIs_{unidade}"
        
        try:
            df_pois = pd.read_excel(self.config_path, sheet_name=sheet_name, engine="openpyxl")
            
            pois = []
            for _, row in df_pois.iterrows():
                poi = {
                    "ponto_interesse": row["ponto_interesse"],
                    "grupo": row["grupo"],
                    "sla_horas": row.get("sla_horas", 0),
                    "threshold_alerta": row.get("threshold_alerta", 10),
                    "ativo": row.get("ativo", True)
                }
                pois.append(poi)
            
            # Filtra apenas POIs ativos
            pois_ativos = [p for p in pois if p["ativo"]]
            
            print(f"POIs carregados para {unidade}: {len(pois_ativos)} ativos")
            return pois_ativos
            
        except Exception as e:
            print(f"Erro ao carregar POIs da unidade {unidade}: {e}")
            # Se não encontrar aba específica, retorna lista vazia
            return []
    
    def carregar_configuracao_email(self) -> Dict[str, Any]:
        """
        Carrega configurações de e-mail.
        
        Returns:
            Dicionário com configurações de e-mail
        """
        try:
            df_email = pd.read_excel(self.config_path, sheet_name="Email_Config", engine="openpyxl")
            
            config_email = {}
            for _, row in df_email.iterrows():
                tipo = row["tipo"]
                config_email[tipo] = {
                    "destinatarios": row["destinatarios"].split(";") if pd.notna(row["destinatarios"]) else [],
                    "assunto_template": row.get("assunto_template", ""),
                    "ativo": row.get("ativo", True)
                }
            
            print(f"Configurações de e-mail carregadas: {len(config_email)} tipos")
            return config_email
            
        except Exception as e:
            print(f"Erro ao carregar configurações de e-mail: {e}")
            # Retorna configuração padrão em caso de erro
            return {
                "falha_sistema": {
                    "destinatarios": [os.getenv("SP_USER", "admin@suzano.com.br")],
                    "assunto_template": "[ERRO] Bot C09 - Falha na Execução",
                    "ativo": True
                },
                "desvio_poi": {
                    "destinatarios": [os.getenv("SP_USER", "admin@suzano.com.br")],
                    "assunto_template": "[ALERTA] Desvio Detectado - {unidade}",
                    "ativo": True
                }
            }
    
    def carregar_credenciais(self) -> Dict[str, str]:
        """
        Carrega credenciais do arquivo .env.
        
        Returns:
            Dicionário com credenciais
        """
        credenciais = {
            "frota_user": os.getenv("FROTA_USER", ""),
            "frota_password": os.getenv("FROTA_PASSWORD", ""),
            "sp_user": os.getenv("SP_USER", ""),
            "sp_password": os.getenv("SP_PASSWORD", ""),
            "chrome_driver_path": os.getenv("CHROME_DRIVER_PATH", ""),
        }
        
        # Valida credenciais obrigatórias
        obrigatorias = ["frota_user", "frota_password", "sp_user", "sp_password", "chrome_driver_path"]
        faltando = [key for key in obrigatorias if not credenciais[key]]
        
        if faltando:
            raise ValueError(f"Credenciais obrigatórias não encontradas no .env: {faltando}")
        
        print("Credenciais carregadas com sucesso")
        return credenciais
    
    def carregar_configuracao_completa(self) -> Dict[str, Any]:
        """
        Carrega configuração completa do sistema.
        
        Returns:
            Dicionário com todas as configurações
        """
        try:
            config = {
                "unidades": self.carregar_unidades(),
                "credenciais": self.carregar_credenciais(),
                "email": self.carregar_configuracao_email(),
                "pois_por_unidade": {}
            }
            
            # Carrega POIs para cada unidade
            for unidade_config in config["unidades"]:
                unidade = unidade_config["unidade"]
                config["pois_por_unidade"][unidade] = self.carregar_pois_unidade(unidade)
            
            print("=== Configuração completa carregada com sucesso ===")
            return config
            
        except Exception as e:
            print(f"ERRO ao carregar configuração completa: {e}")
            raise


# Configurações específicas que não mudam frequentemente
class ConstantesEspecificas:
    """Constantes específicas do sistema que raramente mudam."""
    
    # URLs e endpoints
    FROTALOG_URL = "https://frotalog.com.br/"
    SHAREPOINT_BASE_URL = "https://suzano.sharepoint.com/sites/Controleoperacional"
    SHAREPOINT_DOCS_PATH = "/sites/Controleoperacional/Documentos Compartilhados/Bases de Dados"
    
    # Configurações de execução
    DOWNLOAD_TIMEOUT = 300  # segundos
    MAX_TENTATIVAS_STATUS = 60
    INTERVALO_VERIFICACAO = 10  # segundos
    
    # Paths locais (podem ser configuráveis depois)
    BASE_REPORTS_LOCAL = r"C:\Users\tallespaiva\Suzano S A\Controle operacional - Bases de Dados\CREARE\RRP\C09\2025"
    CAMINHO_REPORTS = r"C:\Users\tallespaiva\Suzano S A\Controle operacional - Bases de Dados\CREARE\RRP\C09\2025\Reports\base de dados reports.xlsx"
    
    # Configurações SharePoint
    LISTA_DESVIOS = "Desvios"
    
    # Meses em português
    MESES_PT = {
        1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
        5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto", 
        9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
    }


# Factory function para facilitar uso
def carregar_config(config_path: str = None) -> Dict[str, Any]:
    """
    Função utilitária para carregar configuração completa.
    
    Args:
        config_path: Caminho opcional para arquivo de configuração
        
    Returns:
        Dicionário com configuração completa
    """
    loader = ConfigurationLoader(config_path)
    return loader.carregar_configuracao_completa()


# Função para validar configuração
def validar_configuracao(config: Dict[str, Any]) -> bool:
    """
    Valida se configuração está completa e correta.
    
    Args:
        config: Configuração a ser validada
        
    Returns:
        True se válida, False caso contrário
    """
    try:
        # Verifica estrutura básica
        campos_obrigatorios = ["unidades", "credenciais", "email", "pois_por_unidade"]
        for campo in campos_obrigatorios:
            if campo not in config:
                print(f"Campo obrigatório ausente: {campo}")
                return False
        
        # Verifica se há pelo menos uma unidade
        if not config["unidades"]:
            print("Nenhuma unidade configurada")
            return False
        
        # Verifica se cada unidade tem POIs
        for unidade_config in config["unidades"]:
            unidade = unidade_config["unidade"]
            if unidade not in config["pois_por_unidade"] or not config["pois_por_unidade"][unidade]:
                print(f"Unidade {unidade} não tem POIs configurados")
                return False
        
        print("Configuração validada com sucesso")
        return True
        
    except Exception as e:
        print(f"Erro na validação da configuração: {e}")
        return False