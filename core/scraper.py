# core/scraper.py - CORRIGIDO PARA CLOUD RUN
"""
Módulo de automação web para download de relatórios C09 do Frotalog.
VERSÃO CORRIGIDA: Funciona tanto local quanto Cloud Run.
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
        Configura opções do Chrome para ambos os ambientes.
        CORRIGIDO: Configurações otimizadas para Cloud Run.
        """
        options = webdriver.ChromeOptions()
        
        if self.is_cloud_run:
            print("🔧 Configurando Chrome para Cloud Run (OTIMIZADO)...")
            
            # Configurações OBRIGATÓRIAS para Cloud Run
            options.add_argument("--headless=new")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--disable-web-security")
            options.add_argument("--disable-features=VizDisplayCompositor")
            
            # OTIMIZAÇÕES DE MEMÓRIA AGRESSIVAS
            options.add_argument("--memory-pressure-off")
            options.add_argument("--disable-background-timer-throttling")
            options.add_argument("--disable-renderer-backgrounding")
            options.add_argument("--disable-backgrounding-occluded-windows")
            options.add_argument("--disable-client-side-phishing-detection")
            options.add_argument("--disable-component-extensions-with-background-pages")
            options.add_argument("--disable-default-apps")
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-plugins")
            options.add_argument("--disable-images")
            options.add_argument("--disable-javascript")  # CRÍTICO: Frotalog não precisa JS para download
            options.add_argument("--disable-sync")
            options.add_argument("--disable-translate")
            options.add_argument("--disable-ipc-flooding-protection")
            
            # LIMITES DE MEMÓRIA RÍGIDOS
            options.add_argument("--max_old_space_size=512")  # 512MB max JS heap
            options.add_argument("--memory-pressure-off")
            options.add_argument("--aggressive-cache-discard")
            options.add_argument("--window-size=1024x768")  # Ainda menor
            
            # DESABILITA RECURSOS PESADOS
            options.add_argument("--disable-features=TranslateUI,BlinkGenPropertyTrees")
            
            # IMPORTANTE: Não definir binary_location no Cloud Run
            # O Chrome é instalado via apt-get no Dockerfile
            
        else:
            print("🔧 Configurando Chrome para ambiente local...")
            options.add_argument("--headless=new")
            options.add_argument("--disable-gpu") 
            options.add_argument("--window-size=1920x1080")
            options.add_argument("--no-sandbox")
        
        # Configurações de download (comum para ambos)
        prefs = {
            "download.prompt_for_download": False,
            "download.default_directory": str(self.pasta_download),
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True,
            "profile.default_content_settings.popups": 0,
        }
        options.add_experimental_option("prefs", prefs)
        
        # Logs reduzidos para Cloud Run
        if self.is_cloud_run:
            options.add_argument("--log-level=3")  # Só erros
            options.add_experimental_option('excludeSwitches', ['enable-logging'])
            options.add_experimental_option('useAutomationExtension', False)
        
        return options
    
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
        # Fecha alertas JavaScript
        try:
            WebDriverWait(driver, 3).until(EC.alert_is_present())
            driver.switch_to.alert.accept()
            print("✅ Alerta JavaScript fechado")
        except TimeoutException:
            pass
        
        # Fecha pop-up de sessão
        try:
            wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//input[@value='Continuar com a sessão atual']")
            )).click()
            print("✅ Pop-up de sessão tratado")
        except TimeoutException:
            print("ℹ️ Nenhum pop-up detectado")
    
    def _navegar_para_c09(self, driver: webdriver.Chrome, wait: WebDriverWait) -> None:
        """Navega até o relatório C09."""
        print("🧭 Navegando para relatório C09...")
        
        # Entra no frame principal
        wait.until(EC.frame_to_be_available_and_switch_to_it((By.NAME, "main")))
        print("✅ Frame 'main' carregado")
        
        # Menu Relatórios > Dirigibilidade
        menu = wait.until(EC.presence_of_element_located((By.XPATH, "//*[@id='menu']/a")))
        submenu = driver.find_element(By.XPATH, "/html/body/form/div[1]/div[1]/table/tbody/tr/td[5]/ul/li[1]/a")
        ActionChains(driver).move_to_element(menu).pause(1).move_to_element(submenu).click().perform()
        print("✅ Menu Dirigibilidade acessado")
        time.sleep(2)
        
        # Clica em C09
        driver.find_element(By.XPATH, "//a[contains(text(), 'C09')]").click()
        print("✅ Relatório C09 selecionado")
        time.sleep(3)
    
    def _selecionar_empresa(self, driver: webdriver.Chrome, wait: WebDriverWait, empresa: str) -> None:
        """Seleciona empresa no dropdown."""
        print(f"🏢 Selecionando empresa: {empresa}")
        
        # Reentra no frame após carregar relatório
        driver.switch_to.default_content()
        wait.until(EC.frame_to_be_available_and_switch_to_it((By.NAME, "main")))
        
        # Seleciona empresa no dropdown
        wait.until(EC.presence_of_element_located((By.ID, "branchId")))
        dropdown_empresa = driver.find_element(By.ID, "branchId")
        
        for option in dropdown_empresa.find_elements(By.TAG_NAME, "option"):
            if empresa in option.text:
                option.click()
                print(f"✅ Empresa '{empresa}' selecionada")
                break
        else:
            raise ValueError(f"Empresa '{empresa}' não encontrada no dropdown")
        
        time.sleep(1)
    
    def _configurar_periodo(self, driver: webdriver.Chrome, wait: WebDriverWait, 
                          data_inicial: datetime, data_final: datetime) -> None:
        """Configura período do relatório."""
        print(f"📅 Configurando período: {data_inicial.date()} a {data_final.date()}")
        
        # Seleciona modo 'Período'
        wait.until(EC.element_to_be_clickable((By.ID, "range"))).click()
        print("✅ Modo 'Período' selecionado")
        
        # Extrai componentes das datas
        dia_ini, mes_ini, ano_ini = str(data_inicial.day), str(data_inicial.month), str(data_inicial.year)
        dia_fim, mes_fim, ano_fim = str(data_final.day), str(data_final.month), str(data_final.year)
        
        # Data inicial
        driver.find_element(By.XPATH, "//*[@id='periodo']/tbody/tr[2]/td[1]/input[1]").clear()
        driver.find_element(By.XPATH, "//*[@id='periodo']/tbody/tr[2]/td[1]/input[1]").send_keys(dia_ini)
        time.sleep(0.3)
        driver.find_element(By.XPATH, "//*[@id='periodo']/tbody/tr[2]/td[1]/input[2]").clear()
        driver.find_element(By.XPATH, "//*[@id='periodo']/tbody/tr[2]/td[1]/input[2]").send_keys(mes_ini)
        time.sleep(0.3)
        driver.find_element(By.XPATH, "//*[@id='periodo']/tbody/tr[2]/td[1]/input[3]").clear()
        driver.find_element(By.XPATH, "//*[@id='periodo']/tbody/tr[2]/td[1]/input[3]").send_keys(ano_ini)
        time.sleep(0.3)
        
        # Data final
        driver.find_element(By.XPATH, "//*[@id='periodo']/tbody/tr[2]/td[2]/input[1]").clear()
        driver.find_element(By.XPATH, "//*[@id='periodo']/tbody/tr[2]/td[2]/input[1]").send_keys(dia_fim)
        time.sleep(0.3)
        driver.find_element(By.XPATH, "//*[@id='periodo']/tbody/tr[2]/td[2]/input[2]").clear()
        driver.find_element(By.XPATH, "//*[@id='periodo']/tbody/tr[2]/td[2]/input[2]").send_keys(mes_fim)
        time.sleep(0.3)
        driver.find_element(By.XPATH, "//*[@id='periodo']/tbody/tr[2]/td[2]/input[3]").clear()
        driver.find_element(By.XPATH, "//*[@id='periodo']/tbody/tr[2]/td[2]/input[3]").send_keys(ano_fim)
        time.sleep(0.3)
        
        print("✅ Período configurado")
    
    def _gerar_relatorio(self, driver: webdriver.Chrome, wait: WebDriverWait) -> None:
        """Configura formato XLSX e gera relatório."""
        print("📊 Configurando formato e gerando relatório...")
        
        # Seleciona formato XLSX
        driver.find_element(By.ID, "typeXLSX").click()
        print("✅ Formato XLSX selecionado")
        
        # Clica em "Visualizar Relatório"
        driver.find_element(By.XPATH,
            "/html/body/table/tbody/tr[2]/td/table/tbody/tr/td/table/tbody/tr/td[1]/table/"
            "tbody/tr[3]/td[2]/table/tbody/tr/td[2]/table/tbody/tr/td/form/table/tbody/"
            "tr[11]/td/table/tbody/tr[1]/td[1]/input"
        ).click()
        print("✅ Botão 'Visualizar Relatório' clicado")
        time.sleep(3)
        
        # Fecha janela de visualização
        WebDriverWait(driver, 15).until(lambda d: len(d.window_handles) > 1)
        original = driver.window_handles[0]
        extra = driver.window_handles[1]
        driver.switch_to.window(extra)
        driver.close()
        driver.switch_to.window(original)
        print("✅ Janela de visualização fechada")
    
    def _aguardar_e_baixar(self, driver: webdriver.Chrome, wait: WebDriverWait) -> None:
        """Aguarda relatório ficar pronto e faz download."""
        print("⏳ Aguardando relatório ficar pronto...")
        
        # Reentra no frame e clica em "Listar Relatórios"
        driver.switch_to.default_content()
        wait.until(EC.frame_to_be_available_and_switch_to_it((By.NAME, "main")))
        
        driver.find_element(By.XPATH,
            "/html/body/table/tbody/tr[1]/td/table/tbody/tr/td[3]/table/tbody/tr[2]/"
            "td/table/tbody/tr/td[1]/table/tbody/tr/td[8]/a"
        ).click()
        print("✅ 'Listar Relatórios' clicado")
        
        # Monitora status até ficar 'Pronto'
        max_tentativas = 30 if not self.is_cloud_run else 45  # Reduzido drasticamente
        intervalo_segundos = 15  # Aumentado intervalo para reduzir requests
        
        for tentativa in range(1, max_tentativas + 1):
            try:
                status = driver.find_element(
                    By.XPATH,
                    "/html/body/table/tbody/tr[2]/td/table/tbody/tr/td/table/tbody/tr/"
                    "td[1]/table/tbody/tr[3]/td[2]/form/table/tbody/tr[2]/"
                    "td/table/tbody/tr[3]/td[8]"
                ).text
                
                if "Pronto" in status:
                    print(f"✅ Relatório pronto (tentativa {tentativa})")
                    
                    # Clica no link de download
                    link = driver.find_element(
                        By.XPATH,
                        "/html/body/table/tbody/tr[2]/td/table/tbody/tr/td/table/tbody/tr/"
                        "td[1]/table/tbody/tr[3]/td[2]/form/table/tbody/tr[2]/"
                        "td/table/tbody/tr[3]/td[1]/a"
                    )
                    link.click()
                    print("✅ Download iniciado")
                    break
                else:
                    if tentativa % 5 == 0:  # Log reduzido
                        print(f"⏳ Tentativa {tentativa}: status '{status}'")
                    
            except NoSuchElementException:
                if tentativa % 10 == 0:  # Log ainda mais reduzido
                    print(f"⏳ Tentativa {tentativa}: aguardando elemento...")
                    
            time.sleep(intervalo_segundos)
        else:
            raise TimeoutException("Relatório não ficou pronto dentro do tempo limite")
    
    def _aguardar_download_completo(self) -> str:
        """Aguarda download ser concluído e retorna caminho do arquivo."""
        print("📥 Aguardando conclusão do download...")
        
        caminho_report = self.pasta_download / "report.xlsx"
        caminho_temp = self.pasta_download / "report.xlsx.crdownload"
        
        segundos = 0
        while ((not caminho_report.exists()) or caminho_temp.exists()) and segundos < self.download_timeout:
            time.sleep(1)
            segundos += 1
            
            # Log progress no Cloud Run
            if self.is_cloud_run and segundos % 30 == 0:
                print(f"📥 Download em progresso... {segundos}s")
        
        if not caminho_report.exists():
            raise FileNotFoundError(f"Download não concluído em {self.download_timeout}s")
        
        # Verifica tamanho do arquivo
        tamanho_mb = caminho_report.stat().st_size / (1024 * 1024)
        print(f"✅ Download finalizado: {caminho_report} ({tamanho_mb:.1f}MB)")
        return str(caminho_report)
    
    def baixar_relatorio_c09(self, empresa_frotalog: str, data_inicial: datetime, data_final: datetime) -> str:
        """
        Download completo do relatório C09.
        CORRIGIDO: Funciona tanto local quanto Cloud Run.
        """
        print(f"🚀 Iniciando download C09: {empresa_frotalog}")
        print(f"📅 Período: {data_inicial.date()} → {data_final.date()}")
        
        driver = None
        try:
            # 1. Cria WebDriver
            driver = self._create_webdriver()
            wait = WebDriverWait(driver, 20)
            
            # 2. Login
            self._fazer_login(driver, wait)
            
            # 3. Navegar para C09
            self._navegar_para_c09(driver, wait)
            
            # 4. Selecionar empresa
            self._selecionar_empresa(driver, wait, empresa_frotalog)
            
            # 5. Configurar período
            self._configurar_periodo(driver, wait, data_inicial, data_final)
            
            # 6. Gerar relatório
            self._gerar_relatorio(driver, wait)
            
            # 7. Aguardar e baixar
            self._aguardar_e_baixar(driver, wait)
            
            # 8. Aguardar conclusão do download
            caminho_arquivo = self._aguardar_download_completo()
            
            print(f"🎉 Download C09 concluído: {empresa_frotalog}")
            return caminho_arquivo
            
        except Exception as e:
            print(f"❌ ERRO no download C09: {e}")
            
            # Diagnóstico adicional para Cloud Run
            if self.is_cloud_run:
                print("🔍 Diagnóstico Cloud Run:")
                print(f"   - Memória disponível: {self._get_memory_info()}")
                print(f"   - Arquivos temp: {list(self.pasta_download.glob('*'))}")
            
            raise
            
        finally:
            if driver:
                try:
                    driver.quit()
                    print("✅ WebDriver fechado")
                except:
                    pass
    
    def _monitorar_memoria(self, fase: str):
        """Monitora uso de memória durante execução."""
        try:
            import psutil
            memory = psutil.virtual_memory()
            used_gb = (memory.total - memory.available) / (1024**3)
            
            if self.is_cloud_run:
                print(f"🔍 {fase}: {memory.percent:.1f}% ({used_gb:.1f}GB usado)")
                
                # ALERTA se passar de 1.5GB no Cloud Run  
                if used_gb > 1.5:
                    print(f"⚠️ ALERTA MEMÓRIA: {used_gb:.1f}GB - próximo do limite!")
                    
        except ImportError:
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