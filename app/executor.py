from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import traceback
import sys
import io
from datetime import datetime
from app.utils.screenshots import save_screenshot
from app.utils.file_utils import save_log
import os

class SeleniumExecutor:
    def _init_(self, headless: bool = True):
        self.headless = headless
        self.driver = None

    def _init_driver(self):
        """Inicializa el navegador Chrome con soporte para Render/Docker y local"""
        chrome_options = Options()
        
        # ✅ Opciones críticas para Render/Docker
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-software-rasterizer")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-setuid-sandbox")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--remote-debugging-port=9222")
        
        # User agent realista
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Preferencias
        chrome_options.add_experimental_option("prefs", {
            "profile.default_content_setting_values.notifications": 2,
            "profile.default_content_settings.popups": 0,
            "download.prompt_for_download": False,
            "safebrowsing.enabled": False
        })
        
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)

        try:
            # ✅ Detectar entorno: Render/Docker vs Local
            is_docker = os.path.exists('/.dockerenv') or os.path.exists('/usr/bin/chromium')
            
            if is_docker:
                # 🐳 Entorno Render/Docker
                chrome_binary = os.getenv('CHROME_BIN', '/usr/bin/chromium')
                chromedriver_path = os.getenv('CHROMEDRIVER_PATH', '/usr/bin/chromedriver')
                
                if not os.path.exists(chrome_binary):
                    raise FileNotFoundError(f"Chrome no encontrado en: {chrome_binary}")
                
                if not os.path.exists(chromedriver_path):
                    raise FileNotFoundError(f"ChromeDriver no encontrado en: {chromedriver_path}")
                
                chrome_options.binary_location = chrome_binary
                service = Service(chromedriver_path)
                
                print(f"🐳 Entorno Docker detectado")
                print(f"   Chrome: {chrome_binary}")
                print(f"   ChromeDriver: {chromedriver_path}")
            else:
                # 💻 Entorno Local
                try:
                    from webdriver_manager.chrome import ChromeDriverManager
                    service = Service(ChromeDriverManager().install())
                    print("💻 Entorno local: usando webdriver-manager")
                except ImportError:
                    # Fallback: intentar usar chromedriver del PATH
                    service = Service()
                    print("💻 Entorno local: usando chromedriver del PATH")
            
            # Inicializar driver
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Configuraciones post-inicialización
            self.driver.set_page_load_timeout(30)
            self.driver.implicitly_wait(5)
            
            print(f"✅ Chrome iniciado correctamente (headless mode)")
            
        except Exception as e:
            error_msg = f"❌ Error al inicializar Chrome: {str(e)}"
            print(error_msg)
            print(f"Detalles: {traceback.format_exc()}")
            raise RuntimeError(error_msg)

    def run_script(self, script: str, test_name: str, browser: str = "chrome", headless: bool = True):
        """Ejecuta un script de Selenium generado por Manus IA"""
        self.headless = headless
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Crear directorios
        os.makedirs("app/results/logs", exist_ok=True)
        os.makedirs("app/results/screenshots", exist_ok=True)
        
        # Limpiar nombre del test
        safe_test_name = test_name.replace(" ", "_").replace("/", "-").replace("\\", "-")[:100]
        
        log_path = f"app/results/logs/{safe_test_name}_{timestamp}.log"
        screenshot_path = f"app/results/screenshots/{safe_test_name}_{timestamp}.png"

        # Buffer para capturar output
        output_buffer = io.StringIO()
        original_stdout = sys.stdout

        try:
            print(f"🚀 Iniciando ejecución: {test_name}")
            print(f"📅 Timestamp: {timestamp}")
            
            # Inicializar navegador
            self._init_driver()
            save_log(safe_test_name, f"=== Inicio: {test_name} ===\nTimestamp: {timestamp}\n")

            # Redirigir stdout para capturar prints del script
            sys.stdout = output_buffer
            
            # Entorno de ejecución
            exec_env = {
                "_builtins": __builtins_,
                "driver": self.driver,
                "By": By,
                "Keys": Keys,
                "WebDriverWait": WebDriverWait,
                "EC": EC,
                "time": time,
                "save_screenshot": lambda: save_screenshot(self.driver, safe_test_name),
                "datetime": datetime,
                "os": os
            }

            print(f"📝 Ejecutando script generado por Manus IA...")
            print("=" * 80)
            
            # Ejecutar script
            exec(script, exec_env)
            
            print("=" * 80)
            print(f"✅ Script completado exitosamente")

            # Restaurar stdout
            sys.stdout = original_stdout

            # Capturar screenshot final
            save_screenshot(self.driver, safe_test_name)
            save_log(safe_test_name, "✅ Ejecución completada exitosamente")

            # Obtener output
            execution_output = output_buffer.getvalue()
            
            # Guardar log
            with open(log_path, 'w', encoding='utf-8') as f:
                f.write(execution_output)

            print(f"✅ Test completado: {test_name}")
            print(f"📄 Log: {log_path}")
            print(f"📸 Screenshot: {screenshot_path}")

            result = {
                "status": "success",
                "test_name": test_name,
                "timestamp": timestamp,
                "log_file": log_path,
                "screenshot": screenshot_path,
                "message": f"✅ Test ejecutado exitosamente\n\n{execution_output[:500]}..."
            }

        except Exception as e:
            # Restaurar stdout
            sys.stdout = original_stdout
            
            error_message = f"❌ Error durante ejecución:\n{str(e)}\n\n{traceback.format_exc()}"
            print(error_message)
            save_log(safe_test_name, error_message)
            
            # Screenshot del error
            if self.driver:
                try:
                    save_screenshot(self.driver, f"{safe_test_name}_ERROR")
                except:
                    pass
            
            # Output parcial
            execution_output = output_buffer.getvalue()
            
            # Guardar log con error
            with open(log_path, 'w', encoding='utf-8') as f:
                f.write(execution_output)
                f.write("\n\n" + error_message)
            
            result = {
                "status": "error",
                "test_name": test_name,
                "timestamp": timestamp,
                "log_file": log_path,
                "screenshot": screenshot_path,
                "message": f"{error_message}\n\nOutput antes del error:\n{execution_output[:300]}..."
            }

        finally:
            # Restaurar stdout
            sys.stdout = original_stdout
            
            # Cerrar navegador
            if self.driver:
                try:
                    print("🔄 Cerrando navegador...")
                    time.sleep(2)
                    self.driver.quit()
                    print("✅ Navegador cerrado")
                except Exception as e:
                    print(f"⚠️ Error al cerrar navegador: {e}")

        return result
