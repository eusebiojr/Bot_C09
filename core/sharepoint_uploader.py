# core/sharepoint_uploader.py
"""
Módulo para upload de arquivos no SharePoint.
Unifica a lógica de upload presente nos scripts RRP/TLS.
"""

from office365.sharepoint.client_context import ClientContext
from office365.runtime.auth.user_credential import UserCredential
from typing import Union
from pathlib import Path


class SharePointUploader:
    """
    Classe para upload de arquivos no SharePoint.
    Abstrai a complexidade das operações de SharePoint.
    """
    
    def __init__(self, site_url: str, username: str, password: str):
        """
        Inicializa uploader do SharePoint.
        
        Args:
            site_url: URL do site SharePoint
            username: Usuário SharePoint
            password: Senha SharePoint
        """
        self.site_url = site_url
        self.username = username
        self.password = password
        self._ctx = None
    
    def _get_context(self) -> ClientContext:
        """Obtém contexto SharePoint (lazy initialization)."""
        if self._ctx is None:
            credentials = UserCredential(self.username, self.password)
            self._ctx = ClientContext(self.site_url).with_credentials(credentials)
        return self._ctx
    
    def _criar_pasta_se_necessario(self, caminho_pasta: str) -> bool:
        """
        Cria pasta no SharePoint se não existir.
        CORRIGIDO: Usa caminhos relativos corretos.
        
        Args:
            caminho_pasta: Caminho da pasta no SharePoint
            
        Returns:
            True se pasta existe ou foi criada com sucesso
        """
        try:
            ctx = self._get_context()
            
            # Remove site URL do caminho se presente
            if caminho_pasta.startswith("/sites/"):
                # Extrai apenas a parte após /sites/SITENAME/
                partes = caminho_pasta.split('/')
                if len(partes) > 3:
                    # Reconstrói caminho relativo: /Documentos Compartilhados/...
                    caminho_relativo = '/' + '/'.join(partes[3:])
                else:
                    caminho_relativo = caminho_pasta
            else:
                caminho_relativo = caminho_pasta
            
            print(f"🔍 Verificando pasta: {caminho_relativo}")
            
            # Tenta acessar a pasta
            pasta = ctx.web.get_folder_by_server_relative_url(caminho_relativo)
            ctx.load(pasta)
            ctx.execute_query()
            print(f"✅ Pasta já existe: {caminho_relativo}")
            return True
            
        except Exception as e:
            print(f"📁 Pasta não existe, criando: {caminho_relativo}")
            return self._criar_pasta_recursiva(ctx, caminho_relativo)

    def _criar_pasta_recursiva(self, ctx, caminho_pasta: str) -> bool:
        """
        Cria pasta recursivamente no SharePoint.
        
        Args:
            ctx: Contexto SharePoint
            caminho_pasta: Caminho relativo da pasta
            
        Returns:
            True se pasta foi criada
        """
        try:
            # Remove barras iniciais/finais e divide o caminho
            caminho_limpo = caminho_pasta.strip('/')
            partes_caminho = caminho_limpo.split('/')
            
            # Inicia da pasta raiz (Documentos Compartilhados)
            pasta_atual = ctx.web.root_folder
            caminho_atual = ""
            
            for i, parte in enumerate(partes_caminho):
                if not parte:
                    continue
                    
                caminho_atual = f"{caminho_atual}/{parte}" if caminho_atual else f"/{parte}"
                
                try:
                    # Verifica se esta parte do caminho existe
                    pasta_teste = ctx.web.get_folder_by_server_relative_url(caminho_atual)
                    ctx.load(pasta_teste)
                    ctx.execute_query()
                    pasta_atual = pasta_teste
                    print(f"✅ Pasta existe: {caminho_atual}")
                    
                except Exception:
                    # Pasta não existe, precisa criar
                    print(f"📁 Criando pasta: {parte} em {caminho_atual.rsplit('/', 1)[0] if '/' in caminho_atual else 'raiz'}")
                    
                    try:
                        pasta_atual = pasta_atual.folders.add(parte)
                        ctx.execute_query()
                        print(f"✅ Pasta criada: {caminho_atual}")
                        
                    except Exception as create_error:
                        print(f"❌ Erro ao criar pasta '{parte}': {create_error}")
                        # Tenta método alternativo
                        return self._criar_pasta_alternativa(ctx, caminho_pasta)
            
            return True
            
        except Exception as e:
            print(f"❌ Erro na criação recursiva: {e}")
            return False

    def _criar_pasta_alternativa(self, ctx, caminho_pasta: str) -> bool:
        """
        Método alternativo para criar pastas (usando lista de documentos).
        
        Args:
            ctx: Contexto SharePoint
            caminho_pasta: Caminho da pasta
            
        Returns:
            True se pasta foi criada
        """
        try:
            print(f"🔄 Tentando método alternativo para: {caminho_pasta}")
            
            # Usa biblioteca de documentos como base
            doc_lib = ctx.web.default_document_library()
            ctx.load(doc_lib)
            ctx.execute_query()
            
            # Remove /Documentos Compartilhados/ do início se presente
            caminho_sem_docs = caminho_pasta
            if caminho_sem_docs.startswith('/Documentos Compartilhados/'):
                caminho_sem_docs = caminho_sem_docs[len('/Documentos Compartilhados/'):]
            elif caminho_sem_docs.startswith('Documentos Compartilhados/'):
                caminho_sem_docs = caminho_sem_docs[len('Documentos Compartilhados/'):]
            
            # Cria pasta na biblioteca de documentos
            partes = caminho_sem_docs.strip('/').split('/')
            pasta_atual = doc_lib.root_folder
            
            for parte in partes:
                if parte:
                    try:
                        pasta_atual = pasta_atual.folders.add(parte)
                        ctx.execute_query()
                        print(f"✅ Pasta alternativa criada: {parte}")
                    except Exception as e:
                        print(f"⚠️ Pasta pode já existir: {parte} ({e})")
            
            return True
            
        except Exception as e:
            print(f"❌ Método alternativo falhou: {e}")
            return False
    
    def _excluir_arquivo_antigo(self, caminho_pasta: str, nome_arquivo: str) -> bool:
        """
        Exclui arquivo antigo se existir.
        
        Args:
            caminho_pasta: Caminho da pasta no SharePoint
            nome_arquivo: Nome do arquivo a excluir
            
        Returns:
            True se arquivo foi excluído ou não existia
        """
        try:
            ctx = self._get_context()
            pasta = ctx.web.get_folder_by_server_relative_url(caminho_pasta)
            arquivos = pasta.files.get().execute_query()
            
            for arquivo in arquivos:
                if arquivo.name == nome_arquivo:
                    print(f"Excluindo arquivo antigo: {nome_arquivo}")
                    arquivo.delete_object()
            
            ctx.execute_query()
            return True
            
        except Exception as e:
            print(f"Erro ao excluir arquivo antigo: {e}")
            return False
    
    def upload_arquivo(self, base_sharepoint: str, ano: str, mes: str, 
                      nome_arquivo: str, conteudo: Union[str, bytes], 
                      is_buffer: bool = True) -> bool:
        """Faz upload de arquivo para SharePoint."""
        try:
            # ✅ MUDANÇA: Usa nova constante
            from config.settings import ConstantesEspecificas
            raiz_docs = ConstantesEspecificas.SHAREPOINT_DOCS_PATH
            
            # Constrói caminho da pasta
            caminho_pasta = f"{raiz_docs}/{base_sharepoint}/{ano}/{mes}"
            
            print(f"Upload para: {caminho_pasta}/{nome_arquivo}")
            
            # 1. Cria pasta se necessário
            if not self._criar_pasta_se_necessario(caminho_pasta):
                print("❌ Falha ao criar/acessar pasta")
                return False
            
            # 2. Exclui arquivo antigo
            if not self._excluir_arquivo_antigo(caminho_pasta, nome_arquivo):
                print("⚠️ Aviso: Não foi possível excluir arquivo antigo")
            
            # 3. Prepara conteúdo para upload
            if is_buffer:
                # Conteúdo já é bytes
                dados_upload = conteudo
            else:
                # Lê arquivo do disco
                with open(conteudo, "rb") as f:
                    dados_upload = f.read()
            
            # 4. Faz upload
            ctx = self._get_context()
            pasta = ctx.web.get_folder_by_server_relative_url(caminho_pasta)
            pasta.upload_file(nome_arquivo, dados_upload).execute_query()
            
            print(f"✅ Upload concluído: {nome_arquivo}")
            return True
            
        except Exception as e:
            print(f"❌ Erro no upload: {e}")
            return False
    
    def upload_arquivo_simples(self, caminho_sharepoint_completo: str, 
                              conteudo: Union[str, bytes], is_buffer: bool = True) -> bool:
        """
        Upload simples com caminho completo.
        
        Args:
            caminho_sharepoint_completo: Caminho completo no SharePoint
            conteudo: Conteúdo do arquivo
            is_buffer: True se conteudo é bytes, False se é caminho
            
        Returns:
            True se upload bem-sucedido
        """
        try:
            # Separa pasta e nome do arquivo
            caminho = Path(caminho_sharepoint_completo)
            caminho_pasta = str(caminho.parent).replace('\\', '/')
            nome_arquivo = caminho.name
            
            # Usa método principal
            # Como o caminho já vem completo, precisamos extrair as partes
            partes = caminho_sharepoint_completo.strip('/').split('/')
            
            if len(partes) >= 3:
                # Assume formato: .../base_sharepoint/ano/mes/arquivo
                base = '/'.join(partes[:-3])
                ano = partes[-3]
                mes = partes[-2]
                
                return self.upload_arquivo(
                    base_sharepoint=base,
                    ano=ano,
                    mes=mes,
                    nome_arquivo=nome_arquivo,
                    conteudo=conteudo,
                    is_buffer=is_buffer
                )
            else:
                raise ValueError("Caminho SharePoint inválido")
                
        except Exception as e:
            print(f"❌ Erro no upload simples: {e}")
            return False
    
    def listar_arquivos(self, caminho_pasta: str) -> list:
        """
        Lista arquivos em uma pasta do SharePoint.
        
        Args:
            caminho_pasta: Caminho da pasta no SharePoint
            
        Returns:
            Lista com nomes dos arquivos
        """
        try:
            ctx = self._get_context()
            pasta = ctx.web.get_folder_by_server_relative_url(caminho_pasta)
            arquivos = pasta.files.get().execute_query()
            
            return [arquivo.name for arquivo in arquivos]
            
        except Exception as e:
            print(f"Erro ao listar arquivos: {e}")
            return []
    
    def excluir_arquivo(self, caminho_arquivo_completo: str) -> bool:
        """
        Exclui arquivo específico do SharePoint.
        
        Args:
            caminho_arquivo_completo: Caminho completo do arquivo
            
        Returns:
            True se arquivo foi excluído
        """
        try:
            ctx = self._get_context()
            arquivo = ctx.web.get_file_by_server_relative_url(caminho_arquivo_completo)
            arquivo.delete_object()
            ctx.execute_query()
            
            print(f"Arquivo excluído: {caminho_arquivo_completo}")
            return True
            
        except Exception as e:
            print(f"Erro ao excluir arquivo: {e}")
            return False


# Factory function para facilitar uso
def criar_uploader(site_url: str = None, username: str = None, password: str = None) -> SharePointUploader:
    """
    Cria uploader SharePoint com configurações padrão.
    
    Args:
        site_url: URL do site (opcional, usa padrão se None)
        username: Usuário (opcional, usa .env se None)  
        password: Senha (opcional, usa .env se None)
        
    Returns:
        Instância configurada do SharePointUploader
    """
    import os
    from config.settings import ConstantesEspecificas
    
    if site_url is None:
        site_url = ConstantesEspecificas.SHAREPOINT_BASE_URL
    
    if username is None:
        username = os.getenv("SP_USER")
    
    if password is None:
        password = os.getenv("SP_PASSWORD")
    
    return SharePointUploader(site_url, username, password)