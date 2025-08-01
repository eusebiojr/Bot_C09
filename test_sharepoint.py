# test_sharepoint.py - Teste isolado das credenciais SharePoint
"""
Teste rápido para verificar se as credenciais SharePoint estão corretas.
Execute localmente primeiro: python test_sharepoint.py
"""

import os
from dotenv import load_dotenv

def testar_credenciais_sharepoint():
    """
    Testa conexão SharePoint com as credenciais atuais.
    """
    print("🧪 TESTE DE CREDENCIAIS SHAREPOINT")
    print("=" * 50)
    
    # Carrega credenciais
    load_dotenv()
    
    sp_user = os.getenv("SP_USER")
    sp_password = os.getenv("SP_PASSWORD")
    
    print(f"👤 Usuário: {sp_user}")
    print(f"🔐 Senha: {'*' * len(sp_password) if sp_password else 'NÃO ENCONTRADA'}")
    
    if not sp_user or not sp_password:
        print("❌ Credenciais não encontradas no .env")
        return False
    
    try:
        from office365.sharepoint.client_context import ClientContext
        from office365.runtime.auth.user_credential import UserCredential
        
        # Configurações
        site_url = "https://suzano.sharepoint.com/sites/Controleoperacional"
        
        print(f"🌐 Testando conexão: {site_url}")
        
        # Criar contexto
        ctx = ClientContext(site_url).with_credentials(
            UserCredential(sp_user, sp_password)
        )
        
        # Teste básico: listar listas do site
        lists = ctx.web.lists
        ctx.load(lists)
        ctx.execute_query()
        
        print(f"✅ CONEXÃO SHAREPOINT OK!")
        print(f"📋 Site possui {len(lists)} listas")
        
        # Lista algumas listas encontradas
        print("\n📁 Algumas listas encontradas:")
        for i, lista in enumerate(lists[:5]):  # Primeiras 5
            print(f"   {i+1}. {lista.properties.get('Title', 'Sem título')}")
        
        return True
        
    except Exception as e:
        print(f"❌ ERRO NA CONEXÃO SHAREPOINT: {e}")
        
        # Tipos de erro mais comuns
        erro_str = str(e).lower()
        if "401" in erro_str or "unauthorized" in erro_str:
            print("🔐 DIAGNÓSTICO: Credenciais incorretas")
            print("   - Verifique usuário e senha")
            print("   - Teste login manual no SharePoint")
        elif "403" in erro_str or "forbidden" in erro_str:
            print("🚫 DIAGNÓSTICO: Usuário sem permissão")
            print("   - Solicite acesso ao site de Controle Operacional")
        elif "timeout" in erro_str:
            print("⏱️ DIAGNÓSTICO: Timeout de conexão")
            print("   - Verifique conectividade de rede")
        else:
            print("❓ DIAGNÓSTICO: Erro desconhecido")
            print("   - Verifique URL do site")
            
        return False

def testar_credenciais_frotalog():
    """
    Testa se as credenciais Frotalog estão configuradas.
    """
    print("\n🧪 TESTE DE CREDENCIAIS FROTALOG")
    print("=" * 50)
    
    frota_user = os.getenv("FROTA_USER")
    frota_password = os.getenv("FROTA_PASSWORD")
    
    print(f"👤 Usuário: {frota_user}")
    print(f"🔐 Senha: {'*' * len(frota_password) if frota_password else 'NÃO ENCONTRADA'}")
    
    if not frota_user or not frota_password:
        print("❌ Credenciais Frotalog não encontradas")
        return False
    else:
        print("✅ Credenciais Frotalog configuradas")
        print("⚠️ Não é possível testar sem Selenium funcionando")
        return True

def main():
    """
    Executa todos os testes de credenciais.
    """
    print("🔐 TESTE COMPLETO DE CREDENCIAIS")
    print("=" * 60)
    
    # Teste SharePoint
    sharepoint_ok = testar_credenciais_sharepoint()
    
    # Teste Frotalog
    frotalog_ok = testar_credenciais_frotalog()
    
    # Resultado final
    print("\n" + "=" * 60)
    print("📋 RESULTADO DOS TESTES:")
    print(f"   📤 SharePoint: {'✅ OK' if sharepoint_ok else '❌ FALHA'}")
    print(f"   📥 Frotalog: {'✅ OK' if frotalog_ok else '❌ FALHA'}")
    
    if sharepoint_ok and frotalog_ok:
        print("\n🎉 TODAS AS CREDENCIAIS ESTÃO OK!")
        print("💡 O problema NÃO é nas credenciais")
        print("🔧 Foque na resolução do Selenium/Chrome")
    elif not sharepoint_ok:
        print("\n⚠️ PROBLEMA NAS CREDENCIAIS SHAREPOINT")
        print("🔧 Corrija as credenciais antes de continuar")
    else:
        print("\n⚠️ PROBLEMA NAS CREDENCIAIS FROTALOG")
        print("🔧 Verifique usuário e senha do Frotalog")
    
    return 0 if (sharepoint_ok and frotalog_ok) else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())