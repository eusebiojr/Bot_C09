# script_gerar_config.py
"""
Script para gerar a planilha de configuração unidades.xlsx
Execute este script uma vez para criar o template inicial.
"""

import pandas as pd
from pathlib import Path


def criar_planilha_configuracao():
    """Cria planilha de configuração inicial do sistema C09."""
    
    # Aba 1: Unidades
    df_unidades = pd.DataFrame([
        {
            "unidade": "RRP",
            "empresa_frotalog": "RB - TRANSP. CELULOSE", 
            "base_sharepoint": "CREARE/RRP/C09",
            "total_veiculos": 91,
            "ativo": True
        },
        {
            "unidade": "TLS", 
            "empresa_frotalog": "TLA - TRANSP. CELULOSE",
            "base_sharepoint": "CREARE/TLS/C09",
            "total_veiculos": 85,
            "ativo": True
        }
    ])
    
    # Aba 2: POIs RRP
    df_pois_rrp = pd.DataFrame([
        {"ponto_interesse": "PA AGUA CLARA", "grupo": "P.A Agua Clara", "sla_horas": 0, "threshold_alerta": 8, "ativo": True},
        {"ponto_interesse": "Carregamento RRp", "grupo": "Carregamento", "sla_horas": 1.0, "threshold_alerta": 8, "ativo": True},
        {"ponto_interesse": "Desc. INO", "grupo": "Descarregamento", "sla_horas": 1.1833, "threshold_alerta": 15, "ativo": True},
        {"ponto_interesse": "Manutenção Campo Grande", "grupo": "Manutenção", "sla_horas": 0, "threshold_alerta": 5, "ativo": True},
        {"ponto_interesse": "Manutencao fabrica", "grupo": "Manutenção", "sla_horas": 0, "threshold_alerta": 5, "ativo": True},
        {"ponto_interesse": "Manutenção Geral JSL RRP", "grupo": "Manutenção", "sla_horas": 0, "threshold_alerta": 5, "ativo": True},
        {"ponto_interesse": "Oficina JSL", "grupo": "Manutenção", "sla_horas": 0, "threshold_alerta": 15, "ativo": True},
        {"ponto_interesse": "Buffer frotas", "grupo": "Parada Operacional", "sla_horas": 0, "threshold_alerta": 5, "ativo": True},
        {"ponto_interesse": "Abastecimento Frotas RRP", "grupo": "Parada Operacional", "sla_horas": 0, "threshold_alerta": 5, "ativo": True},
        {"ponto_interesse": "Carregamento Fabrica RRP", "grupo": "Fabrica", "sla_horas": 1.0, "threshold_alerta": 8, "ativo": True},
        {"ponto_interesse": "Posto Mutum", "grupo": "Parada Operacional", "sla_horas": 0, "threshold_alerta": 5, "ativo": True},
        {"ponto_interesse": "Enlonamento RRP", "grupo": "Parada Operacional", "sla_horas": 0, "threshold_alerta": 5, "ativo": True},
        {"ponto_interesse": "Terminal Inocencia", "grupo": "Terminal", "sla_horas": 1.1833, "threshold_alerta": 15, "ativo": True},
        {"ponto_interesse": "Patio Carregado INO", "grupo": "Parada Operacional", "sla_horas": 0, "threshold_alerta": 5, "ativo": True},
        {"ponto_interesse": "Patio Vazio INO", "grupo": "Parada Operacional", "sla_horas": 0, "threshold_alerta": 5, "ativo": True},
    ])
    
    # Aba 3: POIs TLS  
    df_pois_tls = pd.DataFrame([
        {"ponto_interesse": "EXPEDICAO - CELULOSE - ZONA DE CARREG.", "grupo": "Carregamento", "sla_horas": 1.0, "threshold_alerta": 7, "ativo": True},
        {"ponto_interesse": "Descarga TAP", "grupo": "Terminal", "sla_horas": 0.9167, "threshold_alerta": 7, "ativo": True},
        {"ponto_interesse": "REBUCCI", "grupo": "Manutenção", "sla_horas": 0, "threshold_alerta": 5, "ativo": True},
        {"ponto_interesse": "CEMAVI", "grupo": "Manutenção", "sla_horas": 0, "threshold_alerta": 5, "ativo": True},
        {"ponto_interesse": "FEISCAR", "grupo": "Manutenção", "sla_horas": 0, "threshold_alerta": 5, "ativo": True},
        {"ponto_interesse": "DIESELTRONIC", "grupo": "Manutenção", "sla_horas": 0, "threshold_alerta": 5, "ativo": True},
        {"ponto_interesse": "LM RADIADORES", "grupo": "Manutenção", "sla_horas": 0, "threshold_alerta": 5, "ativo": True},
        {"ponto_interesse": "ALBINO", "grupo": "Manutenção", "sla_horas": 0, "threshold_alerta": 5, "ativo": True},
        {"ponto_interesse": "JDIESEL", "grupo": "Manutenção", "sla_horas": 0, "threshold_alerta": 5, "ativo": True},
        {"ponto_interesse": "TRUCK LAZER", "grupo": "Manutenção", "sla_horas": 0, "threshold_alerta": 5, "ativo": True},
        {"ponto_interesse": "MS3 LAVA JATO", "grupo": "Manutenção", "sla_horas": 0, "threshold_alerta": 5, "ativo": True},
        {"ponto_interesse": "PB LOPES SCANIA", "grupo": "Manutenção", "sla_horas": 0, "threshold_alerta": 5, "ativo": True},
        {"ponto_interesse": "OFICINA CENTRAL JSL", "grupo": "Manutenção", "sla_horas": 0, "threshold_alerta": 13, "ativo": True},
        {"ponto_interesse": "PB Lopes", "grupo": "Manutenção", "sla_horas": 0, "threshold_alerta": 5, "ativo": True},
        {"ponto_interesse": "Manutencao Celulose", "grupo": "Manutenção", "sla_horas": 0, "threshold_alerta": 5, "ativo": True},
        {"ponto_interesse": "AREA EXTERNA SUZANO", "grupo": "Parada Operacional", "sla_horas": 0, "threshold_alerta": 5, "ativo": True},
        {"ponto_interesse": "FILA DE ABASTECIMENTO POSTO SUZANO", "grupo": "Parada Operacional", "sla_horas": 0, "threshold_alerta": 5, "ativo": True},
        {"ponto_interesse": "POSTO DE ABASTECIMENTO", "grupo": "Parada Operacional", "sla_horas": 0, "threshold_alerta": 5, "ativo": True},
        {"ponto_interesse": "Trajeto Posto", "grupo": "Parada Operacional", "sla_horas": 0, "threshold_alerta": 5, "ativo": True},
        {"ponto_interesse": "PA Celulose", "grupo": "P.A Celulose", "sla_horas": 0, "threshold_alerta": 7, "ativo": True},
        {"ponto_interesse": "MONTANINI", "grupo": "Parada Operacional", "sla_horas": 0, "threshold_alerta": 5, "ativo": True},
        {"ponto_interesse": "SELVIRIA", "grupo": "Parada Operacional", "sla_horas": 0, "threshold_alerta": 5, "ativo": True},
        {"ponto_interesse": "Carregamento Fabrica", "grupo": "Fabrica", "sla_horas": 1.0, "threshold_alerta": 7, "ativo": True},
        {"ponto_interesse": "FILA DESCARGA APT", "grupo": "Terminal", "sla_horas": 0.9167, "threshold_alerta": 7, "ativo": True},
        {"ponto_interesse": "Oficina Central JSL", "grupo": "Manutenção", "sla_horas": 0, "threshold_alerta": 13, "ativo": True},
    ])
    
    # Aba 4: Configuração de E-mail
    df_email = pd.DataFrame([
        {
            "tipo": "falha_sistema",
            "destinatarios": "eusebioagj@suzano.com.br",
            "assunto_template": "[ERRO] Bot C09 - Falha na Execução",
            "ativo": True
        },
        {
            "tipo": "desvio_poi",
            "destinatarios": "eusebioagj@suzano.com.br", 
            "assunto_template": "[ALERTA] Desvio Detectado - {unidade}",
            "ativo": True
        }
    ])
    
    # Criar arquivo Excel
    caminho_saida = Path(__file__).parent / "config" / "unidades.xlsx"
    caminho_saida.parent.mkdir(exist_ok=True)
    
    with pd.ExcelWriter(caminho_saida, engine='openpyxl') as writer:
        df_unidades.to_excel(writer, sheet_name='Unidades', index=False)
        df_pois_rrp.to_excel(writer, sheet_name='POIs_RRP', index=False)
        df_pois_tls.to_excel(writer, sheet_name='POIs_TLS', index=False)
        df_email.to_excel(writer, sheet_name='Email_Config', index=False)
    
    print(f"✅ Planilha de configuração criada: {caminho_saida}")
    print("\n📋 Abas criadas:")
    print("   • Unidades: Configuração geral de RRP e TLS")
    print("   • POIs_RRP: Pontos de interesse da unidade RRP")
    print("   • POIs_TLS: Pontos de interesse da unidade TLS")
    print("   • Email_Config: Configurações de e-mail")
    print("\n✏️ Você pode editar esta planilha para:")
    print("   - Ativar/desativar POIs (coluna 'ativo')")
    print("   - Ajustar SLAs (coluna 'sla_horas')")
    print("   - Modificar thresholds de alerta (coluna 'threshold_alerta')")
    print("   - Adicionar novos POIs ou unidades")
    print("   - Configurar destinatários de e-mail")


if __name__ == "__main__":
    criar_planilha_configuracao()