# teste_email.py
"""
Script para testar sistema de e-mails do C09.
Envia e-mails de teste sem afetar o sistema principal.
"""

import sys
from pathlib import Path
from datetime import datetime

# Adiciona diretório ao path
sys.path.append(str(Path(__file__).parent))

def testar_email_configuracao():
    """Testa configuração básica de e-mail."""
    print("🧪 TESTANDO CONFIGURAÇÃO DE E-MAIL")
    print("=" * 50)
    
    try:
        from config.settings import carregar_config
        from core.email_notifier import criar_email_notifier
        
        # Carrega configuração
        config = carregar_config()
        
        # Cria notificador
        notifier = criar_email_notifier(config)
        
        # Teste básico de configuração
        print(f"📧 Usuário: {notifier.username}")
        print(f"📧 Servidor: {notifier.smtp_server}:{notifier.smtp_port}")
        
        # Executa teste de configuração
        sucesso = notifier.testar_configuracao()
        
        if sucesso:
            print("✅ E-mail de teste enviado com sucesso!")
            print("📬 Verifique sua caixa de entrada")
        else:
            print("❌ Falha no envio do e-mail de teste")
            
        return sucesso
        
    except Exception as e:
        print(f"❌ Erro no teste de e-mail: {e}")
        
        # Diagnóstico detalhado
        if "Authentication" in str(e):
            print("\n🔧 DIAGNÓSTICO:")
            print("- Erro de autenticação Outlook")
            print("- Pode precisar de senha de aplicativo")
            print("- Verificar se 2FA está habilitado")
            
        elif "Connection" in str(e):
            print("\n🔧 DIAGNÓSTICO:")
            print("- Erro de conexão SMTP")
            print("- Verificar firewall/proxy")
            print("- Testar conectividade com outlook.office365.com")
            
        return False

def testar_email_alerta_simulado():
    """Simula envio de alerta de desvio."""
    print("\n🧪 TESTANDO ALERTA DE DESVIO SIMULADO")
    print("=" * 50)
    
    try:
        from config.settings import carregar_config
        from core.email_notifier import criar_email_notifier
        
        # Carrega configuração
        config = carregar_config()
        notifier = criar_email_notifier(config)
        
        # Simula alerta de desvio
        sucesso = notifier.enviar_alerta_desvio(
            unidade="RRP",
            poi="PA AGUA CLARA", 
            veiculos=["ABC1234", "DEF5678", "GHI9012"],
            nivel="Tratativa N2",
            grupo="Parada Operacional"
        )
        
        if sucesso:
            print("✅ Alerta de desvio simulado enviado!")
        else:
            print("❌ Falha no envio do alerta simulado")
            
        return sucesso
        
    except Exception as e:
        print(f"❌ Erro no teste de alerta: {e}")
        return False

def testar_email_falha_simulada():
    """Simula envio de falha do sistema."""
    print("\n🧪 TESTANDO FALHA DE SISTEMA SIMULADA")
    print("=" * 50)
    
    try:
        from config.settings import carregar_config
        from core.email_notifier import criar_email_notifier
        
        # Carrega configuração
        config = carregar_config()
        notifier = criar_email_notifier(config)
        
        # Simula falha do sistema
        sucesso = notifier.enviar_falha_sistema(
            erro="Erro simulado para teste",
            contexto="Teste Manual - Sistema C09",
            timestamp=datetime.now()
        )
        
        if sucesso:
            print("✅ Falha de sistema simulada enviada!")
        else:
            print("❌ Falha no envio da falha simulada")
            
        return sucesso
        
    except Exception as e:
        print(f"❌ Erro no teste de falha: {e}")
        return False

def diagnosticar_outlook():
    """Diagnóstica configuração Outlook."""
    print("\n🔍 DIAGNÓSTICO OUTLOOK/EXCHANGE")
    print("=" * 50)
    
    import socket
    import ssl
    
    try:
        # Testa conectividade básica
        print("🔌 Testando conectividade com outlook.office365.com...")
        
        context = ssl.create_default_context()
        with socket.create_connection(("outlook.office365.com", 587), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname="outlook.office365.com") as ssock:
                print("✅ Conexão SSL/TLS estabelecida")
                
        # Testa SMTP básico
        import smtplib
        print("📧 Testando servidor SMTP...")
        
        server = smtplib.SMTP("outlook.office365.com", 587)
        server.starttls()
        print("✅ STARTTLS funcionando")
        server.quit()
        
        print("\n📋 CONFIGURAÇÕES RECOMENDADAS:")
        print("- Servidor: outlook.office365.com")
        print("- Porta: 587")
        print("- Segurança: STARTTLS")
        print("- Autenticação: OAuth2 ou senha de app")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no diagnóstico: {e}")
        
        print("\n🔧 POSSÍVEIS SOLUÇÕES:")
        print("1. Verificar conectividade de rede")
        print("2. Configurar senha de aplicativo no Outlook")
        print("3. Verificar se 2FA está habilitado")
        print("4. Testar com outro provedor de e-mail")
        
        return False

def main():
    """Executa todos os testes de e-mail."""
    print("📧 SISTEMA DE TESTES DE E-MAIL - C09")
    print("=" * 60)
    
    # Menu de opções
    print("\nEscolha o teste:")
    print("1. 🧪 Teste básico de configuração")
    print("2. 🚨 Simular alerta de desvio")
    print("3. ❌ Simular falha do sistema")
    print("4. 🔍 Diagnóstico Outlook")
    print("5. 🚀 Executar todos os testes")
    
    try:
        opcao = input("\nDigite sua opção (1-5): ").strip()
        
        if opcao == "1":
            testar_email_configuracao()
        elif opcao == "2":
            testar_email_alerta_simulado()
        elif opcao == "3":
            testar_email_falha_simulada()
        elif opcao == "4":
            diagnosticar_outlook()
        elif opcao == "5":
            # Executa todos
            resultados = []
            resultados.append(("Diagnóstico", diagnosticar_outlook()))
            resultados.append(("Configuração", testar_email_configuracao()))
            resultados.append(("Alerta Simulado", testar_email_alerta_simulado()))
            resultados.append(("Falha Simulada", testar_email_falha_simulada()))
            
            print("\n📊 RESUMO DOS TESTES:")
            for nome, sucesso in resultados:
                status = "✅" if sucesso else "❌"
                print(f"{nome}: {status}")
        else:
            print("❌ Opção inválida")
            
    except KeyboardInterrupt:
        print("\n\n👋 Teste cancelado pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")

if __name__ == "__main__":
    main()