# teste_sharepoint_fix.py
"""
Teste rápido para verificar se correção SharePoint funciona.
Execute APÓS aplicar a correção no sharepoint_uploader.py
"""

import os
import sys
from pathlib import Path

# Adiciona path do projeto
sys.path.insert(0, str(Path(__file__).parent))

def testar_criacao_pasta():
    """Testa criação de pasta SharePoint com nova lógica."""
    print("🧪 TESTANDO CORREÇÃO SHAREPOINT")
    print("=" * 50)
    
    try:
        from core.sharepoint_uploader import SharePointUploader
        
        # Carrega credenciais
        from dotenv import load_dotenv
        load_dotenv()
        
        username = os.getenv("SP_USER")
        password = os.getenv("SP_PASSWORD")
        
        if not username or not password:
            print("❌ Credenciais SharePoint não encontradas no .env")
            return False
        
        print(f"👤 Usuário: {username}")
        
        # Cria uploader
        uploader = SharePointUploader(
            site_url="https://suzano.sharepoint.com/sites/Controleoperacional",
            username=username,
            password=password
        )
        
        # Testa criação de pasta simples
        caminho_teste = "/sites/Controleoperacional/Documentos Compartilhados/Teste_BOT/CREARE/RRP/C09/2025/07. Julho"
        
        print(f"📁 Testando criação: {caminho_teste}")
        
        sucesso = uploader._criar_pasta_se_necessario(caminho_teste)
        
        if sucesso:
            print("✅ CORREÇÃO FUNCIONOU!")
            print("✅ Pasta criada/verificada com sucesso")
            return True
        else:
            print("❌ Correção não funcionou")
            return False
            
    except Exception as e:
        print(f"❌ ERRO no teste: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Executa teste."""
    print("🔧 TESTE DE CORREÇÃO - SHAREPOINT UPLOADER")
    print("=" * 60)
    
    sucesso = testar_criacao_pasta()
    
    print("\n" + "=" * 60)
    if sucesso:
        print("🎉 CORREÇÃO APLICADA COM SUCESSO!")
        print("✅ Agora você pode executar o sistema normalmente")
        print("\n🚀 PRÓXIMOS PASSOS:")
        print("1. Execute: python main.py")  
        print("2. Monitore se upload funciona")
    else:
        print("❌ CORREÇÃO NÃO FUNCIONOU")
        print("🔧 Verifique se aplicou corretamente no sharepoint_uploader.py")
    
    return 0 if sucesso else 1

if __name__ == "__main__":
    sys.exit(main())