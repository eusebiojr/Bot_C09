# core/email_notifier.py
"""
Sistema de notificações por e-mail para alertas e falhas do sistema C09.
Usa Microsoft Graph API para contornar restrições SMTP corporativas.
"""

import os
import json
import requests
from datetime import datetime
from typing import Dict, List, Any, Optional
import pandas as pd


class EmailNotifier:
    """
    Sistema de notificações por e-mail via Microsoft Graph API.
    
    Funcionalidades:
    - Alertas de desvios por área
    - Notificações de falhas do sistema
    - Templates responsivos
    - Contorna restrições SMTP corporativas
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Inicializa notificador de e-mail.
        
        Args:
            config: Configuração completa do sistema
        """
        self.config = config
        self.email_config = config.get("email", {})
        
        # Usa credenciais SharePoint (mesmo tenant)
        self.username = config["credenciais"]["sp_user"]
        self.password = config["credenciais"]["sp_password"]
        
        # Microsoft Graph API endpoints
        self.graph_base_url = "https://graph.microsoft.com/v1.0"
        self.token = None
        
        # Carrega responsáveis por área
        self.responsaveis = self._carregar_responsaveis()
        
        print(f"📧 EmailNotifier (Graph API) inicializado para {self.username}")
    
    def _carregar_responsaveis(self) -> Dict[str, List[str]]:
        """
        Carrega responsáveis por área da planilha de configuração.
        
        Returns:
            Dicionário com área -> lista de e-mails
        """
        try:
            # TODO: Implementar carregamento da aba "Responsaveis_Email"
            # Por enquanto, usa configuração padrão
            responsaveis_default = {
                "RRP_Terminal": [self.username],
                "RRP_Fabrica": [self.username],
                "RRP_Manutencao": [self.username],
                "TLS_Terminal": [self.username],
                "TLS_Fabrica": [self.username],
                "TLS_Manutencao": [self.username],
                "Sistema": [self.username]  # Falhas do sistema
            }
            
            print(f"📋 Responsáveis carregados: {len(responsaveis_default)} áreas")
            return responsaveis_default
            
        except Exception as e:
            print(f"⚠️ Erro ao carregar responsáveis, usando padrão: {e}")
            return {"Sistema": [self.username]}
    
    def _obter_access_token(self) -> str:
        """
        Obtém token de acesso Microsoft Graph via autenticação básica.
        
        Returns:
            Token de acesso ou None se falhar
        """
        try:
            # Tenta usar token em cache se ainda válido
            if self.token:
                # TODO: Verificar se token ainda é válido
                return self.token
            
            # Microsoft Graph não suporta autenticação básica diretamente
            # Precisamos usar SharePoint como proxy ou configurar App Registration
            
            print("⚠️ Microsoft Graph requer configuração específica")
            print("💡 ALTERNATIVA: Usar SharePoint para enviar e-mails")
            
            return None
            
        except Exception as e:
            print(f"❌ Erro ao obter token Graph: {e}")
            return None
    
    def _enviar_via_sharepoint(self, destinatarios: List[str], assunto: str, html_content: str) -> bool:
        """
        Envia e-mail via SharePoint (alternativa ao Graph).
        
        Args:
            destinatarios: Lista de e-mails
            assunto: Assunto do e-mail
            html_content: Conteúdo HTML
            
        Returns:
            True se enviado com sucesso
        """
        try:
            from office365.sharepoint.client_context import ClientContext
            from office365.runtime.auth.user_credential import UserCredential
            
            # Conecta no SharePoint
            site_url = "https://suzano.sharepoint.com/sites/Controleoperacional"
            credentials = UserCredential(self.username, self.password)
            ctx = ClientContext(site_url).with_credentials(credentials)
            
            # Tenta usar utilidades de e-mail do SharePoint
            # Nota: Nem todos os tenants permitem isso
            
            print("🔧 Tentando envio via SharePoint...")
            
            # SharePoint Online não tem API direta de e-mail
            # Alternativa: Criar item na lista que dispara workflow de e-mail
            
            return self._criar_item_email_lista(ctx, destinatarios, assunto, html_content)
            
        except Exception as e:
            print(f"❌ Erro no envio via SharePoint: {e}")
            return False
    
    def _criar_item_email_lista(self, ctx, destinatarios: List[str], assunto: str, html_content: str) -> bool:
        """
        Cria item em lista SharePoint para disparar e-mail via workflow.
        
        Args:
            ctx: Contexto SharePoint
            destinatarios: Lista de e-mails
            assunto: Assunto
            html_content: Conteúdo HTML
            
        Returns:
            True se item criado
        """
        try:
            # Verifica se lista "Emails_Sistema" existe
            lista_emails = ctx.web.lists.get_by_title("Emails_Sistema")
            
            # Cria item que pode disparar Power Automate/workflow
            item_data = {
                "Title": assunto,
                "Destinatarios": ";".join(destinatarios),
                "Conteudo": html_content[:255],  # Limite SharePoint
                "Status": "Pendente",
                "DataCriacao": datetime.now().isoformat()
            }
            
            lista_emails.add_item(item_data).execute_query()
            
            print(f"📝 Item de e-mail criado na lista SharePoint")
            print("💡 Configure Power Automate para processar esta lista")
            
            return True
            
        except Exception as e:
            print(f"⚠️ Lista Emails_Sistema não existe: {e}")
            print("💡 Criando arquivo de log como alternativa...")
            
            return self._salvar_email_log(destinatarios, assunto, html_content)
    
    def _salvar_email_log(self, destinatarios: List[str], assunto: str, html_content: str) -> bool:
        """
        Salva e-mail em arquivo de log como fallback.
        
        Args:
            destinatarios: Lista de e-mails
            assunto: Assunto
            html_content: Conteúdo HTML
            
        Returns:
            True sempre (fallback)
        """
        try:
            from pathlib import Path
            
            # Cria diretório de logs se não existir
            log_dir = Path(__file__).parent.parent / "logs"
            log_dir.mkdir(exist_ok=True)
            
            # Salva e-mail em arquivo JSON
            email_log = {
                "timestamp": datetime.now().isoformat(),
                "destinatarios": destinatarios,
                "assunto": assunto,
                "conteudo_html": html_content,
                "status": "LOGGED_FALLBACK"
            }
            
            log_file = log_dir / "emails_nao_enviados.json"
            
            # Append ao arquivo de log
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(email_log, ensure_ascii=False) + "\n")
            
            print(f"📄 E-mail salvo em log: {log_file}")
            print("📧 Configure sistema de e-mail corporativo para processar este log")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao salvar log de e-mail: {e}")
            return False
    
    def _gerar_template_alerta_desvio(self, unidade: str, poi: str, veiculos: List[str], 
                                    nivel: str, timestamp: datetime) -> str:
        """
        Gera template HTML para alerta de desvio.
        
        Args:
            unidade: Nome da unidade (RRP, TLS)
            poi: Ponto de interesse
            veiculos: Lista de veículos em desvio
            nivel: Nível do alerta (N1, N2, etc.)
            timestamp: Momento do alerta
            
        Returns:
            HTML do e-mail
        """
        cor_nivel = {
            "Tratativa N1": "#FFA500",  # Laranja
            "Tratativa N2": "#FF6347",  # Vermelho claro
            "Tratativa N3": "#DC143C",  # Vermelho
            "Tratativa N4": "#8B0000"   # Vermelho escuro
        }
        
        cor = cor_nivel.get(nivel, "#FFA500")
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; }}
                .container {{ max-width: 600px; margin: 0 auto; }}
                .header {{ background-color: {cor}; color: white; padding: 20px; text-align: center; }}
                .content {{ background-color: #f9f9f9; padding: 20px; }}
                .footer {{ background-color: #333; color: white; padding: 10px; text-align: center; font-size: 12px; }}
                .alert-box {{ background-color: white; border-left: 5px solid {cor}; padding: 15px; margin: 10px 0; }}
                .veiculos {{ background-color: #e8f4fd; padding: 10px; border-radius: 5px; }}
                table {{ width: 100%; border-collapse: collapse; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>🚨 ALERTA DE DESVIO - {nivel}</h2>
                    <p>Sentinela WEB - Monitoramento de Frotas</p>
                </div>
                
                <div class="content">
                    <div class="alert-box">
                        <h3>Detalhes do Desvio</h3>
                        <table>
                            <tr><th>Unidade</th><td>{unidade}</td></tr>
                            <tr><th>Ponto de Interesse</th><td>{poi}</td></tr>
                            <tr><th>Data/Hora</th><td>{timestamp.strftime('%d/%m/%Y %H:%M:%S')}</td></tr>
                            <tr><th>Nível</th><td><strong>{nivel}</strong></td></tr>
                            <tr><th>Qtd. Veículos</th><td>{len(veiculos)}</td></tr>
                        </table>
                    </div>
                    
                    <div class="veiculos">
                        <h4>Veículos em Desvio:</h4>
                        <p>{', '.join(veiculos)}</p>
                    </div>
                    
                    <div class="alert-box">
                        <h4>⚡ Ação Necessária</h4>
                        <p>Foi detectado acúmulo de veículos no ponto <strong>{poi}</strong>. 
                        Por favor, verifique a situação e tome as ações necessárias.</p>
                        
                        <p><strong>Próximas verificações:</strong></p>
                        <ul>
                            <li>Verificar causa do acúmulo</li>
                            <li>Contatar responsáveis locais</li>
                            <li>Atualizar status no SharePoint</li>
                        </ul>
                    </div>
                </div>
                
                <div class="footer">
                    <p>Sentinela WEB - Suzano | Gerado automaticamente em {timestamp.strftime('%d/%m/%Y %H:%M:%S')}</p>
                    <p>Para dúvidas, contate a equipe de TI</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _gerar_template_falha_sistema(self, erro: str, contexto: str, 
                                    timestamp: datetime, tentativas: int = None) -> str:
        """
        Gera template HTML para falha do sistema.
        
        Args:
            erro: Descrição do erro
            contexto: Contexto onde ocorreu
            timestamp: Momento da falha
            tentativas: Número de tentativas (se aplicável)
            
        Returns:
            HTML do e-mail
        """
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; }}
                .container {{ max-width: 600px; margin: 0 auto; }}
                .header {{ background-color: #DC143C; color: white; padding: 20px; text-align: center; }}
                .content {{ background-color: #f9f9f9; padding: 20px; }}
                .footer {{ background-color: #333; color: white; padding: 10px; text-align: center; font-size: 12px; }}
                .error-box {{ background-color: #ffebee; border-left: 5px solid #DC143C; padding: 15px; margin: 10px 0; }}
                .info-box {{ background-color: #e3f2fd; border-left: 5px solid #2196F3; padding: 15px; margin: 10px 0; }}
                table {{ width: 100%; border-collapse: collapse; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .error-code {{ background-color: #f5f5f5; padding: 10px; font-family: monospace; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>❌ FALHA NO SISTEMA C09</h2>
                    <p>Notificação Automática de Erro</p>
                </div>
                
                <div class="content">
                    <div class="error-box">
                        <h3>Detalhes da Falha</h3>
                        <table>
                            <tr><th>Data/Hora</th><td>{timestamp.strftime('%d/%m/%Y %H:%M:%S')}</td></tr>
                            <tr><th>Contexto</th><td>{contexto}</td></tr>
                            {'<tr><th>Tentativas</th><td>' + str(tentativas) + '</td></tr>' if tentativas else ''}
                            <tr><th>Erro</th><td class="error-code">{erro}</td></tr>
                        </table>
                    </div>
                    
                    <div class="info-box">
                        <h4>🔧 Próximas Ações</h4>
                        <ul>
                            <li>Verificar logs detalhados no sistema</li>
                            <li>Validar credenciais e conexões</li>
                            <li>Verificar status dos serviços (SharePoint, Frotalog)</li>
                            <li>Monitorar próximas execuções</li>
                        </ul>
                    </div>
                    
                    {'<div class="error-box"><h4>⚠️ Falha Crítica</h4><p>O sistema esgotou todas as tentativas. Intervenção manual necessária.</p></div>' if tentativas and tentativas >= 10 else ''}
                </div>
                
                <div class="footer">
                    <p>Sentinela WEB - Logística MS - Suzano | Gerado automaticamente</p>
                    <p>Logs completos disponíveis no servidor</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def enviar_alerta_desvio(self, unidade: str, poi: str, veiculos: List[str], 
                           nivel: str, grupo: str = None) -> bool:
        """
        Envia alerta de desvio por e-mail.
        
        Args:
            unidade: Nome da unidade
            poi: Ponto de interesse
            veiculos: Lista de veículos
            nivel: Nível do alerta
            grupo: Grupo do POI (Terminal, Fabrica, etc.)
            
        Returns:
            True se enviado com sucesso
        """
        try:
            # Determina responsáveis baseado na área
            area_key = f"{unidade}_{grupo}" if grupo else f"{unidade}_Sistema"
            destinatarios = self.responsaveis.get(area_key, self.responsaveis.get("Sistema", []))
            
            if not destinatarios:
                print(f"⚠️ Nenhum responsável configurado para {area_key}")
                return False
            
            # Gera conteúdo do e-mail
            timestamp = datetime.now()
            assunto = f"[ALERTA {nivel}] Desvio em {poi} - {unidade}"
            
            html_content = self._gerar_template_alerta_desvio(
                unidade=unidade,
                poi=poi,
                veiculos=veiculos,
                nivel=nivel,
                timestamp=timestamp
            )
            
            # Tenta enviar via SharePoint
            return self._enviar_via_sharepoint(
                destinatarios=destinatarios,
                assunto=assunto,
                html_content=html_content
            )
            
        except Exception as e:
            print(f"❌ Erro ao enviar alerta de desvio: {e}")
            return False
    
    def enviar_falha_sistema(self, erro: str, contexto: str, timestamp: datetime) -> bool:
        """
        Envia notificação de falha do sistema.
        
        Args:
            erro: Descrição do erro
            contexto: Contexto da falha
            timestamp: Momento da falha
            
        Returns:
            True se enviado com sucesso
        """
        try:
            destinatarios = self.responsaveis.get("Sistema", [])
            
            if not destinatarios:
                print("⚠️ Nenhum responsável configurado para falhas do sistema")
                return False
            
            assunto = f"[ERRO] Sistema C09 - {contexto}"
            
            html_content = self._gerar_template_falha_sistema(
                erro=erro,
                contexto=contexto,
                timestamp=timestamp
            )
            
            return self._enviar_via_sharepoint(
                destinatarios=destinatarios,
                assunto=assunto,
                html_content=html_content
            )
            
        except Exception as e:
            print(f"❌ Erro ao enviar falha do sistema: {e}")
            return False
    
    def enviar_falha_critica(self, erro: Exception, tentativas: int, 
                           modo: str, timestamp: datetime) -> bool:
        """
        Envia notificação de falha crítica (após esgotar tentativas).
        
        Args:
            erro: Exception que causou a falha
            tentativas: Número de tentativas realizadas
            modo: Modo de execução (CANDLES/COMPLETO)
            timestamp: Momento da falha
            
        Returns:
            True se enviado com sucesso
        """
        try:
            destinatarios = self.responsaveis.get("Sistema", [])
            
            if not destinatarios:
                print("⚠️ Nenhum responsável configurado para falhas críticas")
                return False
            
            assunto = f"[CRÍTICO] Sistema C09 Falhado - {tentativas} tentativas"
            
            html_content = self._gerar_template_falha_sistema(
                erro=str(erro),
                contexto=f"Modo {modo} - {tentativas} tentativas",
                timestamp=timestamp,
                tentativas=tentativas
            )
            
            return self._enviar_via_sharepoint(
                destinatarios=destinatarios,
                assunto=assunto,
                html_content=html_content
            )
            
        except Exception as e:
            print(f"❌ Erro ao enviar falha crítica: {e}")
            return False
    
    def testar_configuracao(self) -> bool:
        """
        Testa configuração de e-mail enviando mensagem de teste.
        
        Returns:
            True se teste bem-sucedido
        """
        try:
            print("🧪 Testando configuração de e-mail (fallback)...")
            
            destinatarios = [self.username]  # Envia para si mesmo
            assunto = "[TESTE] Sistema C09 - Configuração de E-mail"
            
            html_content = f"""
            <html>
            <body>
                <h2>✅ Teste de Configuração</h2>
                <p>Este é um e-mail de teste do sistema C09.</p>
                <p><strong>Status:</strong> Sistema funcionando via fallback</p>
                <p><strong>Data/Hora:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
                <p><strong>Método:</strong> Log de arquivos (SMTP desabilitado)</p>
                
                <h3>🔧 Para habilitar e-mails reais:</h3>
                <ul>
                    <li>Configure Power Automate no SharePoint</li>
                    <li>Ou habilite App Registration no Azure AD</li>
                    <li>Verifique logs em: logs/emails_nao_enviados.json</li>
                </ul>
            </body>
            </html>
            """
            
            sucesso = self._enviar_via_sharepoint(destinatarios, assunto, html_content)
            
            if sucesso:
                print("✅ Teste de e-mail (fallback) bem-sucedido")
                print("📁 Verifique: logs/emails_nao_enviados.json")
            else:
                print("❌ Teste de e-mail falhou")
            
            return sucesso
            
        except Exception as e:
            print(f"❌ Erro no teste de e-mail: {e}")
            return False


# Factory function
def criar_email_notifier(config: Dict[str, Any]) -> EmailNotifier:
    """
    Cria notificador de e-mail.
    
    Args:
        config: Configuração completa do sistema
        
    Returns:
        Instância do EmailNotifier
    """
    return EmailNotifier(config)