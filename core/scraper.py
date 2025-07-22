# core/scraper.py
"""
Módulo de automação web para download de relatórios C09 do Frotalog.
Substitui as funções baixar_relatorio_c09() duplicadas em RRP/TLS.
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
    Configurável para diferentes empresas (RRP, TLS, etc.).
    """
    
    def __init__(self, chrome_driver_path: str, download_timeout: int = 300):
        """
        Inicializa o scraper.
        
        Args:
            chrome_driver_path: Caminho para chromedriver.exe
            download_timeout: Timeout em segundos para download
        """
        self.chrome_driver_path = self._validate_chrome_driver(chrome_driver_path)
        self.download_timeout = download_timeout
        
        # Usa diretório temporário para downloads (funciona local + nuvem)
        import tempfile
        self.pasta_download = Path(tempfile.gettempdir()) / "c09_downloads"
        self.pasta_download.mkdir(exist_ok=True)
        print(f"Pasta de downloads: {self.pasta_download}")
        
    def _validate_chrome_driver(self, path: str) -> str:
        """Valida e resolve caminho do ChromeDriver."""
        if not path:
            raise ValueError("CHROME_DRIVER_PATH não definido no .env")
            
        p = Path(path)
        if not p.is_absolute():
            p = Path(__file__).parent.parent.joinpath(p).resolve()
            
        if not p.is_file():
            raise FileNotFoundError(f"ChromeDriver não encontrado em '{p}'")
            
        return str(p)
    
    def _setup_chrome_options(self) -> webdriver.ChromeOptions:
        """Configura opções do Chrome para automação."""
        options = webdriver.ChromeOptions()
        
        # Execução em background (descomente para headless)
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920x1080")
        options.add_argument("--no-sandbox")
        
        # Configurações de download automático
        prefs = {
            "download.prompt_for_download": False,
            "download.default_directory": str(self.pasta_download),
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        }
        options.add_experimental_option("prefs", prefs)
        
        return options
    
    def _fazer_login(self, driver: webdriver.Chrome, wait: WebDriverWait) -> None:
        """Realiza login no Frotalog."""
        print("Fazendo login no Frotalog...")
        driver.get("https://frotalog.com.br/")
        time.sleep(2)
        
        # Preenche credenciais
        driver.find_element(By.ID, "userName").send_keys(os.getenv("FROTA_USER"))
        driver.find_element(By.NAME, "password").send_keys(os.getenv("FROTA_PASSWORD"))
        driver.find_element(By.XPATH, "//input[contains(@src, 'btn_ok.gif')]").click()
        print("Login enviado.")
        
        # Trata possíveis alertas/pop-ups
        self._tratar_popups(driver, wait)
        
    def _tratar_popups(self, driver: webdriver.Chrome, wait: WebDriverWait) -> None:
        """Trata alertas e pop-ups de sessão."""
        # Fecha alertas JavaScript
        try:
            WebDriverWait(driver, 3).until(EC.alert_is_present())
            driver.switch_to.alert.accept()
            print("Alerta JavaScript fechado.")
        except TimeoutException:
            pass
        
        # Fecha pop-up de sessão
        try:
            wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//input[@value='Continuar com a sessão atual']")
            )).click()
            print("Pop-up de sessão tratado.")
        except TimeoutException:
            print("Nenhum pop-up detectado.")
    
    def _navegar_para_c09(self, driver: webdriver.Chrome, wait: WebDriverWait) -> None:
        """Navega até o relatório C09."""
        print("Navegando para relatório C09...")
        
        # Entra no frame principal
        wait.until(EC.frame_to_be_available_and_switch_to_it((By.NAME, "main")))
        print("Frame 'main' carregado.")
        
        # Menu Relatórios > Dirigibilidade
        menu = wait.until(EC.presence_of_element_located((By.XPATH, "//*[@id='menu']/a")))
        submenu = driver.find_element(By.XPATH, "/html/body/form/div[1]/div[1]/table/tbody/tr/td[5]/ul/li[1]/a")
        ActionChains(driver).move_to_element(menu).pause(1).move_to_element(submenu).click().perform()
        print("Entrou em Dirigibilidade.")
        time.sleep(2)
        
        # Clica em C09
        driver.find_element(By.XPATH, "//a[contains(text(), 'C09')]").click()
        print("Relatório C09 selecionado.")
        time.sleep(3)
    
    def _selecionar_empresa(self, driver: webdriver.Chrome, wait: WebDriverWait, empresa: str) -> None:
        """Seleciona empresa no dropdown."""
        print(f"Selecionando empresa: {empresa}")
        
        # Reentra no frame após carregar relatório
        driver.switch_to.default_content()
        wait.until(EC.frame_to_be_available_and_switch_to_it((By.NAME, "main")))
        
        # Seleciona empresa no dropdown
        wait.until(EC.presence_of_element_located((By.ID, "branchId")))
        dropdown_empresa = driver.find_element(By.ID, "branchId")
        
        for option in dropdown_empresa.find_elements(By.TAG_NAME, "option"):
            if empresa in option.text:
                option.click()
                print(f"Empresa '{empresa}' selecionada.")
                break
        else:
            raise ValueError(f"Empresa '{empresa}' não encontrada no dropdown")
        
        time.sleep(1)
    
    def _configurar_periodo(self, driver: webdriver.Chrome, wait: WebDriverWait, 
                          data_inicial: datetime, data_final: datetime) -> None:
        """Configura período do relatório."""
        print(f"Configurando período: {data_inicial.date()} a {data_final.date()}")
        
        # Seleciona modo 'Período'
        wait.until(EC.element_to_be_clickable((By.ID, "range"))).click()
        print("Modo 'Período' selecionado.")
        
        # Extrai componentes das datas
        dia_ini, mes_ini, ano_ini = str(data_inicial.day), str(data_inicial.month), str(data_inicial.year)
        dia_fim, mes_fim, ano_fim = str(data_final.day), str(data_final.month), str(data_final.year)
        
        # Data inicial
        driver.find_element(By.XPATH, "//*[@id='periodo']/tbody/tr[2]/td[1]/input[1]").clear()
        driver.find_element(By.XPATH, "//*[@id='periodo']/tbody/tr[2]/td[1]/input[1]").send_keys(dia_ini)
        time.sleep(0.5)
        driver.find_element(By.XPATH, "//*[@id='periodo']/tbody/tr[2]/td[1]/input[2]").clear()
        driver.find_element(By.XPATH, "//*[@id='periodo']/tbody/tr[2]/td[1]/input[2]").send_keys(mes_ini)
        time.sleep(0.5)
        driver.find_element(By.XPATH, "//*[@id='periodo']/tbody/tr[2]/td[1]/input[3]").clear()
        driver.find_element(By.XPATH, "//*[@id='periodo']/tbody/tr[2]/td[1]/input[3]").send_keys(ano_ini)
        time.sleep(0.5)
        
        # Data final
        driver.find_element(By.XPATH, "//*[@id='periodo']/tbody/tr[2]/td[2]/input[1]").clear()
        driver.find_element(By.XPATH, "//*[@id='periodo']/tbody/tr[2]/td[2]/input[1]").send_keys(dia_fim)
        time.sleep(0.5)
        driver.find_element(By.XPATH, "//*[@id='periodo']/tbody/tr[2]/td[2]/input[2]").clear()
        driver.find_element(By.XPATH, "//*[@id='periodo']/tbody/tr[2]/td[2]/input[2]").send_keys(mes_fim)
        time.sleep(0.5)
        driver.find_element(By.XPATH, "//*[@id='periodo']/tbody/tr[2]/td[2]/input[3]").clear()
        driver.find_element(By.XPATH, "//*[@id='periodo']/tbody/tr[2]/td[2]/input[3]").send_keys(ano_fim)
        time.sleep(0.5)
        
        print("Período configurado.")
    
    def _gerar_relatorio(self, driver: webdriver.Chrome, wait: WebDriverWait) -> None:
        """Configura formato XLSX e gera relatório."""
        print("Configurando formato e gerando relatório...")
        
        # Seleciona formato XLSX
        driver.find_element(By.ID, "typeXLSX").click()
        print("Formato XLSX selecionado.")
        
        # Clica em "Visualizar Relatório"
        driver.find_element(By.XPATH,
            "/html/body/table/tbody/tr[2]/td/table/tbody/tr/td/table/tbody/tr/td[1]/table/"
            "tbody/tr[3]/td[2]/table/tbody/tr/td[2]/table/tbody/tr/td/form/table/tbody/"
            "tr[11]/td/table/tbody/tr[1]/td[1]/input"
        ).click()
        print("Botão 'Visualizar Relatório' clicado.")
        time.sleep(2)
        
        # Fecha janela de visualização
        WebDriverWait(driver, 15).until(lambda d: len(d.window_handles) > 1)
        original = driver.window_handles[0]
        extra = driver.window_handles[1]
        driver.switch_to.window(extra)
        driver.close()
        driver.switch_to.window(original)
        print("Janela de visualização fechada.")
    
    def _aguardar_e_baixar(self, driver: webdriver.Chrome, wait: WebDriverWait) -> None:
        """Aguarda relatório ficar pronto e faz download."""
        print("Aguardando relatório ficar pronto...")
        
        # Reentra no frame e clica em "Listar Relatórios"
        driver.switch_to.default_content()
        wait.until(EC.frame_to_be_available_and_switch_to_it((By.NAME, "main")))
        
        driver.find_element(By.XPATH,
            "/html/body/table/tbody/tr[1]/td/table/tbody/tr/td[3]/table/tbody/tr[2]/"
            "td/table/tbody/tr/td[1]/table/tbody/tr/td[8]/a"
        ).click()
        print("Clicou em 'Listar Relatórios'.")
        
        # Monitora status até ficar 'Pronto'
        max_tentativas = 60
        intervalo_segundos = 10
        
        for tentativa in range(1, max_tentativas + 1):
            try:
                status = driver.find_element(
                    By.XPATH,
                    "/html/body/table/tbody/tr[2]/td/table/tbody/tr/td/table/tbody/tr/"
                    "td[1]/table/tbody/tr[3]/td[2]/form/table/tbody/tr[2]/"
                    "td/table/tbody/tr[3]/td[8]"
                ).text
                
                if "Pronto" in status:
                    print(f"Relatório pronto na tentativa {tentativa}.")
                    
                    # Clica no link de download
                    link = driver.find_element(
                        By.XPATH,
                        "/html/body/table/tbody/tr[2]/td/table/tbody/tr/td/table/tbody/tr/"
                        "td[1]/table/tbody/tr[3]/td[2]/form/table/tbody/tr[2]/"
                        "td/table/tbody/tr[3]/td[1]/a"
                    )
                    link.click()
                    print("Download iniciado.")
                    break
                else:
                    print(f"Tentativa {tentativa}: status '{status}' - aguardando...")
                    
            except NoSuchElementException:
                print(f"Tentativa {tentativa}: elemento status não encontrado.")
                
            time.sleep(intervalo_segundos)
        else:
            raise TimeoutException("Relatório não ficou pronto dentro do tempo limite.")
    
    def _aguardar_download_completo(self) -> str:
        """Aguarda download ser concluído e retorna caminho do arquivo."""
        print("Aguardando conclusão do download...")
        
        caminho_report = self.pasta_download / "report.xlsx"
        caminho_temp = self.pasta_download / "report.xlsx.crdownload"
        
        segundos = 0
        while ((not caminho_report.exists()) or caminho_temp.exists()) and segundos < self.download_timeout:
            time.sleep(1)
            segundos += 1
        
        if not caminho_report.exists():
            raise FileNotFoundError("Download não concluído dentro do tempo limite.")
        
        print(f"Download finalizado: {caminho_report}")
        return str(caminho_report)
    
    def baixar_relatorio_c09(self, empresa_frotalog: str, data_inicial: datetime, data_final: datetime) -> str:
        """
        Download completo do relatório C09.
        
        Args:
            empresa_frotalog: Nome da empresa no Frotalog (ex: "RB - TRANSP. CELULOSE")
            data_inicial: Data início do período
            data_final: Data fim do período
            
        Returns:
            str: Caminho do arquivo report.xlsx baixado
            
        Raises:
            Exception: Se houver erro em qualquer etapa
        """
        options = self._setup_chrome_options()
        service = Service(self.chrome_driver_path)
        driver = webdriver.Chrome(service=service, options=options)
        wait = WebDriverWait(driver, 20)
        
        try:
            print(f"=== Iniciando download C09: {empresa_frotalog} ===")
            
            # 1. Login
            self._fazer_login(driver, wait)
            
            # 2. Navegar para C09
            self._navegar_para_c09(driver, wait)
            
            # 3. Selecionar empresa
            self._selecionar_empresa(driver, wait, empresa_frotalog)
            
            # 4. Configurar período
            self._configurar_periodo(driver, wait, data_inicial, data_final)
            
            # 5. Gerar relatório
            self._gerar_relatorio(driver, wait)
            
            # 6. Aguardar e baixar
            self._aguardar_e_baixar(driver, wait)
            
            # 7. Aguardar conclusão do download
            caminho_arquivo = self._aguardar_download_completo()
            
            print(f"=== Download C09 concluído com sucesso ===")
            return caminho_arquivo
            
        except Exception as e:
            print(f"ERRO no download C09: {e}")
            raise
            
        finally:
            driver.quit()


# Factory function para compatibilidade com código existente
def criar_scraper(chrome_driver_path: str = None, download_timeout: int = 300) -> FrotalogScraper:
    """
    Cria instância do scraper com configurações do .env.
    Mantém compatibilidade com código existente.
    """
    if chrome_driver_path is None:
        chrome_driver_path = os.getenv("CHROME_DRIVER_PATH", "")
    
    return FrotalogScraper(chrome_driver_path, download_timeout)