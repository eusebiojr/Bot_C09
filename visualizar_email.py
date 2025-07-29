# visualizar_email.py
"""
Script para visualizar e-mails salvos em logs como se fossem reais.
Abre e-mails HTML no navegador para visualização.
"""

import json
import tempfile
import webbrowser
from pathlib import Path
from datetime import datetime

def listar_emails_salvos():
    """Lista todos os e-mails salvos em logs."""
    log_file = Path("logs/emails_nao_enviados.json")
    
    if not log_file.exists():
        print("❌ Nenhum e-mail encontrado em logs/emails_nao_enviados.json")
        return []
    
    emails = []
    try:
        with open(log_file, "r", encoding="utf-8") as f:
            for linha in f:
                if linha.strip():
                    email = json.loads(linha)
                    emails.append(email)
        
        print(f"📧 {len(emails)} e-mail(s) encontrado(s)")
        return emails
        
    except Exception as e:
        print(f"❌ Erro ao ler logs: {e}")
        return []

def mostrar_lista_emails(emails):
    """Mostra lista de e-mails para seleção."""
    print("\n📋 E-MAILS SALVOS:")
    print("=" * 60)
    
    for i, email in enumerate(emails, 1):
        timestamp = email.get("timestamp", "")
        if timestamp:
            # Converte timestamp para formato legível
            try:
                dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                timestamp_str = dt.strftime("%d/%m/%Y %H:%M:%S")
            except:
                timestamp_str = timestamp
        else:
            timestamp_str = "Data desconhecida"
        
        assunto = email.get("assunto", "Sem assunto")
        destinatarios = email.get("destinatarios", [])
        
        print(f"{i}. {timestamp_str}")
        print(f"   📧 Para: {', '.join(destinatarios)}")
        print(f"   📝 Assunto: {assunto}")
        print()

def visualizar_email_html(email):
    """Abre e-mail HTML no navegador."""
    try:
        html_content = email.get("conteudo_html", "")
        
        if not html_content:
            print("❌ Conteúdo HTML não encontrado neste e-mail")
            return False
        
        # Cria arquivo temporário HTML
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
            f.write(html_content)
            temp_file = f.name
        
        # Abre no navegador padrão
        webbrowser.open(f'file://{temp_file}')
        
        print(f"🌐 E-mail aberto no navegador: {temp_file}")
        print("💡 O arquivo temporário será removido quando fechar o navegador")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao abrir e-mail: {e}")
        return False

def imprimir_detalhes_email(email):
    """Imprime detalhes do e-mail no console."""
    print("\n📧 DETALHES DO E-MAIL:")
    print("=" * 50)
    
    print(f"⏰ Timestamp: {email.get('timestamp', 'N/A')}")
    print(f"👥 Destinatários: {', '.join(email.get('destinatarios', []))}")
    print(f"📝 Assunto: {email.get('assunto', 'N/A')}")
    print(f"📊 Status: {email.get('status', 'N/A')}")
    
    # Mostra início do conteúdo HTML
    html_content = email.get("conteudo_html", "")
    if html_content:
        # Extrai só o texto visível (sem tags HTML)
        import re
        texto_limpo = re.sub(r'<[^>]+>', '', html_content)
        texto_limpo = re.sub(r'\s+', ' ', texto_limpo).strip()
        
        print(f"\n📄 Prévia do conteúdo:")
        print("-" * 30)
        print(texto_limpo[:500] + "..." if len(texto_limpo) > 500 else texto_limpo)

def main():
    """Menu principal para visualizar e-mails."""
    print("📧 VISUALIZADOR DE E-MAILS SALVOS - Sistema C09")
    print("=" * 60)
    
    # Lista e-mails salvos
    emails = listar_emails_salvos()
    
    if not emails:
        print("\n💡 DICA: Execute 'python teste_email.py' para gerar e-mails de teste")
        return
    
    # Mostra lista
    mostrar_lista_emails(emails)
    
    while True:
        try:
            print("OPÇÕES:")
            print("1-N. Selecionar e-mail para visualizar")
            print("0. Sair")
            
            opcao = input("\nDigite sua opção: ").strip()
            
            if opcao == "0":
                print("👋 Saindo...")
                break
            
            try:
                indice = int(opcao) - 1
                if 0 <= indice < len(emails):
                    email_selecionado = emails[indice]
                    
                    # Sub-menu para o e-mail selecionado
                    print(f"\n📧 E-MAIL SELECIONADO: {email_selecionado.get('assunto', 'N/A')}")
                    print("1. 🌐 Abrir no navegador (HTML)")
                    print("2. 📄 Mostrar detalhes no console")
                    print("3. 🔙 Voltar à lista")
                    
                    sub_opcao = input("Escolha: ").strip()
                    
                    if sub_opcao == "1":
                        visualizar_email_html(email_selecionado)
                    elif sub_opcao == "2":
                        imprimir_detalhes_email(email_selecionado)
                    elif sub_opcao == "3":
                        continue
                    else:
                        print("❌ Opção inválida")
                else:
                    print("❌ Número inválido")
            except ValueError:
                print("❌ Digite um número válido")
                
        except KeyboardInterrupt:
            print("\n\n👋 Saindo...")
            break
        except Exception as e:
            print(f"❌ Erro: {e}")

if __name__ == "__main__":
    main()