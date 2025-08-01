# core/scraper.py - CORRIGIDO PARA CLOUD RUN
"""
Módulo de automação web para download de relatórios C09 do Frotalog.
VERSÃO CORRIGIDA: Funciona tanto local quanto Cloud Run com validações robustas.
"""

import os
import time
from datetime import datetime
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains


class FrotalogScraper:
    """
    Scraper genérico para download de relatórios C09 do Frotalog.
    CORRIGIDO: Funciona local + Cloud Run sem problemas.
    """
    
    def __init__(self, chrome_driver_path: str, download_timeout: int = 300):
        """
        Inicializa o scraper.
        
        Args:
            chrome_driver_path: Caminho para chromedriver.exe (ignorado no Cloud Run)
            download_timeout: Timeout em segundos para download
        """
        self.chrome_driver_path = chrome_driver_path  # Mantém para compatibilidade
        self.download_timeout = download_timeout
        
        # Detecta ambiente
        self.is_cloud_run = os.getenv("K_SERVICE") is not None
        
        # Pasta de downloads
        import tempfile
        self.pasta_download = Path(tempfile.gettempdir()) / "c09_downloads"
        self.pasta_download.mkdir(exist_ok=True)
        
        if self.is_cloud_run:
            print(f"🌐 CLOUD RUN detectado - Downloads: {self.pasta_download}")
        else:
            print(f"💻 AMBIENTE LOCAL - Downloads: {self.pasta_download}")
    
    def _get_chrome_options(self) -> webdriver.ChromeOptions:
        """
        Configurações Chrome ULTRA-ESTÁVEIS para Cloud Run.
        VERSÃO ANTI-CRASH.
        """
        options = webdriver.ChromeOptions()
        
        if self.is_cloud_run:
            print("🔧 Chrome Cloud Run - Configurações ANTI-CRASH...")
            
            # OBRIGATÓRIAS para Cloud Run
            options.add_argument("--headless=new")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            
            # ANTI-CRASH CRÍTICAS
            options.add_argument("--disable-features=TranslateUI")
            options.add_argument("--disable-features=BlinkGenPropertyTrees")
            options.add_argument("--disable-ipc-flooding-protection")
            options.add_argument("--disable-renderer-backgrounding")
            options.add_argument("--disable-backgrounding-occluded-windows")
            options.add_argument("--disable-client-side-phishing-detection")
            options.add_argument("--disable-component-extensions-with-background-pages")
            options.add_argument("--disable-extensions-http-throttling")
            options.add_argument("--disable-field-trial-config")
            options.add_argument("--disable-back-forward-cache")
            options.add_argument("--disable-hang-monitor")
            options.add_argument("--disable-prompt-on-repost")
            options.add_argument("--disable-domain-reliability")
            options.add_argument("--disable-component-update")
            
            # MEMÓRIA E CRASH PROTECTION
            options.add_argument("--memory-pressure-off")
            options.add_argument("--max_old_space_size=128")  # REDUZIDO para 128MB
            options.add_argument("--aggressive-cache-discard")
            options.add_argument("--window-size=800x600")
            
            # TIMEOUTS RÍGIDOS
            options.add_argument("--timeout=20000")  # 20s max
            options.add_argument("--page-load-strategy=eager")  # Não espera tudo carregar
            
            # DESABILITA TUDO DESNECESSÁRIO
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-plugins")
            options.add_argument("--disable-images")
            options.add_argument("--disable-javascript")
            options.add_argument("--disable-css")
            options.add_argument("--disable-fonts")
            options.add_argument("--disable-background-networking")
            options.add_argument("--disable-sync")
            options.add_argument("--disable-translate")
            options.add_argument("--disable-web-security")
            
            # LOGS MÍNIMOS
            options.add_argument("--log-level=3")
            options.add_argument("--silent")
            options.add_experimental_option('excludeSwitches', ['enable-logging'])
            options.add_experimental_option('useAutomationExtension', False)
            
            # CONFIGURAÇÕES DE PROCESSO
            options.add_argument("--single-process")  # CRÍTICO: Processo único
            options.add_argument("--no-zygote")       # CRÍTICO: Sem processo zygote
            
        else:
            # Local - configuração normal
            print("🔧 Configurando Chrome para ambiente local...")
            options.add_argument("--headless=new")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920x1080")
            options.add_argument("--no-sandbox")
        
        # Downloads (comum)
        prefs = {
            "download.prompt_for_download": False,
            "download.default_directory": str(self.pasta_download),
            "download.directory_upgrade": True,
            "safebrowsing.enabled": False,
            "profile.default_content_settings.popups": 0,
            "profile.default_content_setting_values.notifications": 2,  # Bloquear notificações
            "profile.managed_default_content_settings.images": 2,       # Bloquear imagens
        }
        options.add_experimental_option("prefs", prefs)
        
        return options
    
    def _verificar_driver_ativo(self, driver) -> bool:
        """Verifica se driver ainda está ativo."""
        try:
            _ = driver.current_url
            return True
        except:
            return False
    
    def _create_webdriver(self) -> webdriver.Chrome:
        """
        Cria WebDriver adequado para o ambiente.
        CORRIGIDO: Cloud Run não usa Service, local sim.
        """
        options = self._get_chrome_options()
        
        if self.is_cloud_run:
            # Cloud Run: Chrome gerenciado pelo sistema, sem Service
            try:
                driver = webdriver.Chrome(options=options)
                print("✅ ChromeDriver inicializado no Cloud Run")
                return driver
            except Exception as e:
                print(f"❌ Erro ao inicializar Chrome no Cloud Run: {e}")
                print("🔧 Verificando se Chrome está instalado...")
                
                # Diagnóstico
                chrome_paths = [
                    "/usr/bin/google-chrome",
                    "/usr/bin/google-chrome-stable",
                    "/usr/bin/chromium",
                    "/usr/bin/chromium-browser"
                ]
                
                for path in chrome_paths:
                    if os.path.exists(path):
                        print(f"✅ Chrome encontrado: {path}")
                        options.binary_location = path
                        try:
                            driver = webdriver.Chrome(options=options)
                            print(f"✅ ChromeDriver inicializado com {path}")
                            return driver
                        except Exception as e2:
                            print(f"❌ Falha com {path}: {e2}")
                            continue
                
                raise Exception("Chrome não encontrado no Cloud Run")
        
        else:
            # Ambiente local: Usa ChromeDriver Service
            if not os.path.exists(self.chrome_driver_path):
                raise FileNotFoundError(f"ChromeDriver não encontrado: {self.chrome_driver_path}")
            
            service = Service(self.chrome_driver_path)
            driver = webdriver.Chrome(service=service, options=options)
            print("✅ ChromeDriver inicializado no ambiente local")
            return driver
    
    def _fazer_login(self, driver: webdriver.Chrome, wait: WebDriverWait) -> None:
        """Realiza login no Frotalog."""
        print("🔐 Fazendo login no Frotalog...")
        driver.get("https://frotalog.com.br/")
        time.sleep(3)  # Aguarda carregamento
        
        # Preenche credenciais
        driver.find_element(By.ID, "userName").send_keys(os.getenv("FROTA_USER"))
        driver.find_element(By.NAME, "password").send_keys(os.getenv("FROTA_PASSWORD"))
        driver.find_element(By.XPATH, "//input[contains(@src, 'btn_ok.gif')]").click()
        print("✅ Login enviado")
        
        # Trata possíveis alertas/pop-ups
        self._tratar_popups(driver, wait)
    
    def _tratar_popups(self, driver: webdriver.Chrome, wait: WebDriverWait) -> None:
        """Trata alertas e pop-ups de sessão."""
        try:
            # Aguarda e trata pop-up de sessão
            popup = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@value='SIM']")))
            popup.click()
            print("✅ Pop-up de sessão tratado")
        except TimeoutException:
            print("Nenhum pop-up detectado. Seguindo normalmente.")
    
    def _navegar_para_c09(self, driver: webdriver.Chrome, wait: WebDriverWait) -> None:
        """Navega para o relatório C09."""
        print("🧭 Navegando para relatório C09...")
        
        # Aguarda frame principal
        wait.until(EC.frame_to_be_available_and_switch_to_it((By.NAME, "main")))
        print("✅ Frame 'main' carregado")

        # HOVER em "Relatórios" e clica em "Dirigibilidade"
        menu = wait.until(EC.presence_of_element_located((By.XPATH, "//*[@id='menu']/a")))
        submenu = driver.find_element(By.XPATH, "/html/body/form/div[1]/div[1]/table/tbody/tr/td[5]/ul/li[1]/a")
        ActionChains(driver).move_to_element(menu).pause(1).move_to_element(submenu).click().perform()
        print("✅ Menu Dirigibilidade acessado")
        time.sleep(2)

        # Clica em C09
        driver.find_element(By.XPATH, "//a[contains(text(), 'C09')]").click()
        print("✅ Relatório C09 selecionado")
        time.sleep(3)
    
    def _selecionar_empresa(self, driver: webdriver.Chrome, wait: WebDriverWait, empresa_frotalog: str) -> None:
        """Seleciona empresa no dropdown."""
        print(f"🏢 Selecionando empresa: {empresa_frotalog}")
        
        # Reentra no frame principal
        driver.switch_to.default_content()
        wait.until(EC.frame_to_be_available_and_switch_to_it((By.NAME, "main")))
        print("✅ Reentrou no frame 'main' após carregar o relatório")

        # Seleciona empresa
        wait.until(EC.presence_of_element_located((By.ID, "branchId")))
        empresa = driver.find_element(By.ID, "branchId")
        for option in empresa.find_elements(By.TAG_NAME, "option"):
            if empresa_frotalog in option.text:
                option.click()
                break
        print(f"✅ Empresa '{empresa_frotalog}' selecionada")
        time.sleep(1)
    
    def _configurar_periodo(self, driver: webdriver.Chrome, wait: WebDriverWait, 
                          data_inicial: datetime, data_final: datetime) -> None:
        """Configura período do relatório."""
        print(f"📅 Configurando período: {data_inicial.strftime('%Y-%m-%d')} a {data_final.strftime('%Y-%m-%d')}")
        
        # Seleciona modo 'Período'
        wait.until(EC.element_to_be_clickable((By.ID, "range"))).click()
        print("✅ Modo 'Período' selecionado")

        # Preenche data inicial
        campo_inicial = driver.find_element(By.ID, "initDate")
        campo_inicial.clear()
        campo_inicial.send_keys(data_inicial.strftime("%d/%m/%Y"))

        # Preenche data final
        campo_final = driver.find_element(By.ID, "endDate")
        campo_final.clear()
        campo_final.send_keys(data_final.strftime("%d/%m/%Y"))
        
        print("✅ Período configurado")
    
    def _gerar_relatorio(self, driver: webdriver.Chrome, wait: WebDriverWait) -> None:
        """Gera o relatório."""
        print("📊 Configurando formato e gerando relatório...")
        
        # Seleciona formato XLSX
        formato = driver.find_element(By.ID, "fileFormat")
        for option in formato.find_elements(By.TAG_NAME, "option"):
            if "XLSX" in option.text:
                option.click()
                break
        print("✅ Formato XLSX selecionado")

        # Clica em "Visualizar Relatório"
        driver.find_element(By.ID, "buttonVisualize").click()
        print("✅ Botão 'Visualizar Relatório' clicado")
        time.sleep(5)

        # Fecha janela de visualização se aparecer
        try:
            driver.switch_to.window(driver.window_handles[-1])
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
            print("✅ Janela de visualização fechada")
        except:
            pass

        # Volta para frame principal
        driver.switch_to.default_content()
        wait.until(EC.frame_to_be_available_and_switch_to_it((By.NAME, "main")))
    
    def _aguardar_e_baixar(self, driver: webdriver.Chrome, wait: WebDriverWait) -> None:
        """Aguarda relatório ficar pronto e baixa."""
        print("⏳ Aguardando relatório ficar pronto...")
        
        # Clica em "Listar Relatórios"
        driver.find_element(By.ID, "buttonListReports").click()
        print("✅ 'Listar Relatórios' clicado")

        # Aguarda relatório aparecer na lista
        max_tentativas = 30
        for tentativa in range(1, max_tentativas + 1):
            try:
                time.sleep(10)  # Aguarda 10s entre tentativas
                
                # Atualiza lista
                driver.find_element(By.ID, "buttonListReports").click()
                
                # Procura link de download
                links = driver.find_elements(By.XPATH, "//a[contains(@href, 'downloadReport')]")
                if links:
                    print(f"✅ Relatório pronto (tentativa {tentativa})")
                    
                    # Clica no primeiro link encontrado
                    links[0].click()
                    print("✅ Download iniciado")
                    break
                else:
                    print(f"⏳ Tentativa {tentativa}/{max_tentativas} - aguardando...")
                    
            except Exception as e:
                print(f"⚠️ Erro na tentativa {tentativa}: {e}")
                
        else:
            raise TimeoutException("Relatório não ficou pronto após 30 tentativas")
    
    def _aguardar_download_completo(self) -> str:
        """
        Aguarda download completar com validação agressiva.
        VERSÃO CORRIGIDA: Com validações robustas.
        """
        print("📥 Aguardando conclusão do download...")
        
        arquivo_encontrado = None
        inicio = time.time()
        
        while time.time() - inicio < self.download_timeout:
            # Procura por arquivos na pasta de download
            arquivos = list(self.pasta_download.glob("*.xlsx"))
            
            if arquivos:
                # Pega o arquivo mais recente
                arquivo_mais_recente = max(arquivos, key=lambda f: f.stat().st_mtime)
                
                # Verifica se não é um arquivo temporário (.crdownload, .tmp)
                if not arquivo_mais_recente.name.endswith(('.crdownload', '.tmp')):
                    arquivo_encontrado = arquivo_mais_recente
                    break
            
            time.sleep(2)
        
        # ===== VALIDAÇÕES CRÍTICAS (ADICIONADAS) =====
        if arquivo_encontrado:
            tamanho = arquivo_encontrado.stat().st_size
            print(f"📁 Download encontrado: {arquivo_encontrado.name} ({tamanho} bytes)")
            
            if tamanho == 0:
                print("❌ ERRO: Arquivo baixado está vazio")
                raise ValueError("Arquivo baixado está vazio")
            
            if tamanho < 1000:  # Menos de 1KB é suspeito
                print(f"⚠️ AVISO: Arquivo muito pequeno: {tamanho} bytes")
            
            print(f"✅ Download validado: {arquivo_encontrado}")
            return str(arquivo_encontrado)
        else:
            print("❌ ERRO: Download não completou - arquivo não encontrado")
            raise FileNotFoundError("Download não completou - arquivo não encontrado")
        # ===== FIM DAS VALIDAÇÕES =====
    
    def baixar_relatorio_c09(self, empresa_frotalog: str, data_inicial: datetime, data_final: datetime) -> str:
        """
        Download com proteção anti-crash.
        """
        driver = None
        max_tentativas = 3  # Máximo 3 tentativas
        
        for tentativa in range(1, max_tentativas + 1):
            try:
                print(f"🚀 Tentativa {tentativa}/{max_tentativas} - Download C09: {empresa_frotalog}")
                
                # Criar novo driver a cada tentativa
                if driver:
                    try:
                        driver.quit()
                    except:
                        pass
                
                driver = self._create_webdriver()
                
                # Configurar timeouts mais conservadores
                if self.is_cloud_run:
                    wait = WebDriverWait(driver, 10)  # REDUZIDO: 10s
                    driver.set_page_load_timeout(20)  # REDUZIDO: 20s
                    print("🔧 Timeouts Cloud Run ultra-conservadores")
                else:
                    wait = WebDriverWait(driver, 30)
                    driver.set_page_load_timeout(60)
                
                # Execução com verificação de crash
                self._fazer_login(driver, wait)
                
                # Verificar se driver ainda está ativo
                if not self._verificar_driver_ativo(driver):
                    raise Exception("Driver crashou após login")
                
                self._navegar_para_c09(driver, wait)
                
                if not self._verificar_driver_ativo(driver):
                    raise Exception("Driver crashou após navegação")
                
                self._selecionar_empresa(driver, wait, empresa_frotalog)
                self._configurar_periodo(driver, wait, data_inicial, data_final)
                self._gerar_relatorio(driver, wait)
                
                if not self._verificar_driver_ativo(driver):
                    raise Exception("Driver crashou após gerar relatório")
                
                self._aguardar_e_baixar(driver, wait)
                caminho_arquivo = self._aguardar_download_completo()
                
                print(f"✅ Tentativa {tentativa} bem-sucedida!")
                return caminho_arquivo
                
            except Exception as e:
                print(f"❌ Tentativa {tentativa} falhou: {e}")
                
                if tentativa == max_tentativas:
                    print(f"💥 Todas as {max_tentativas} tentativas falharam")
                    raise
                else:
                    print(f"🔄 Aguardando 10s antes da próxima tentativa...")
                    time.sleep(10)
                
            finally:
                if driver and tentativa == max_tentativas:
                    try:
                        driver.quit()
                        print("✅ WebDriver fechado")
                    except:
                        pass


# Factory function (mantém compatibilidade)
def criar_scraper(chrome_driver_path: str = None, download_timeout: int = 300) -> FrotalogScraper:
    """
    Cria instância do scraper com configurações do .env.
    CORRIGIDO: Funciona local + Cloud Run.
    """
    if chrome_driver_path is None:
        chrome_driver_path = os.getenv("CHROME_DRIVER_PATH", "")
    
    return FrotalogScraper(chrome_driver_path, download_timeout)