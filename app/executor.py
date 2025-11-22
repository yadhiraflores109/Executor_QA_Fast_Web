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

    def __init__(self, headless: bool = True):
        """Constructor corregido"""
        self.headless = headless
        self.driver = None

    def _init_driver(self):
        """Inicializa el navegador Chrome para Render, Docker o local"""

        chrome_options = Options()

        # Modo headless seguro
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-software-rasterizer")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--remote-debugging-port=9222")

        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)

        # Preferencias del perfil
        chrome_options.add_experimental_option(
            "prefs",
            {
                "profile.default_content_setting_values.notifications": 2,
                "profile.default_content_settings.popups": 0,
                "download.prompt_for_download": False,
                "safebrowsing.enabled": False
            }
        )

        try:
            # Detectar entorno
            is_docker = os.path.exists('/.dockerenv') or os.path.exists('/usr/bin/chromium')

            if is_docker:
                print("🐳 Entorno Docker detectado")

                chrome_binary = os.getenv('CHROME_BIN', '/usr/bin/chromium')
                chromedriver_path = os.getenv('CHROMEDRIVER_PATH', '/usr/bin/chromedriver')

                if not os.path.exists(chrome_binary):
                    raise FileNotFoundError(f"Chrome no encontrado en: {chrome_binary}")

                if not os.path.exists(chromedriver_path):
                    raise FileNotFoundError(f"ChromeDriver no encontrado en: {chromedriver_path}")

                chrome_options.binary_location = chrome_binary
                service = Service(chromedriver_path)

            else:
                print("💻 Entorno local detectado")

                try:
                    from webdriver_manager.chrome import ChromeDriverManager
                    service = Service(ChromeDriverManager().install())
                except ImportError:
                    service = Service()

            # Iniciar driver
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.set_page_load_timeout(30)
            self.driver.implicitly_wait(5)

            print("✅ Chrome iniciado correctamente en modo headless")

        except Exception as e:
            error_msg = f"❌ Error al inicializar Chrome: {str(e)}"
            print(error_msg)
            print(traceback.format_exc())
            raise RuntimeError(error_msg)

    def run_script(self, script: str, test_name: str, browser: str = "chrome", headless: bool = True):
        """Ejecuta un script de Selenium generado por el agente"""

        self.headless = headless
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Asegurar directorios correctos
        os.makedirs("app/results/logs", exist_ok=True)
        os.makedirs("app/results/screenshots", exist_ok=True)

        # Nombre seguro del archivo
        safe_test_name = (
            test_name.replace(" ", "_")
            .replace("/", "-")
            .replace("\\", "-")
        )[:100]

        log_path = f"app/results/logs/{safe_test_name}_{timestamp}.log"
        screenshot_path = f"app/results/screenshots/{safe_test_name}_{timestamp}.png"

        # Capturar stdout
        output_buffer = io.StringIO()
        original_stdout = sys.stdout

        try:
            print(f"🚀 Ejecutando test: {test_name}")
            print(f"🕒 Timestamp: {timestamp}")

            # Inicializar navegador
            self._init_driver()
            save_log(safe_test_name, f"=== Inicio ejecución: {test_name} ===\nTimestamp: {timestamp}\n")

            # Redirigir stdout
            sys.stdout = output_buffer

            # Entorno seguro del script
            exec_env = {
                "__builtins__": __builtins__,  # ← CORREGIDO
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

            print("📝 Ejecutando script generado...")
            print("=" * 80)

            exec(script, exec_env)

            print("=" * 80)
            print("✅ Script finalizado sin errores")

            # Restaurar stdout
            sys.stdout = original_stdout

            save_screenshot(self.driver, safe_test_name)
            save_log(safe_test_name, "✅ Ejecución completada")

            execution_output = output_buffer.getvalue()

            # Guardar log limpio
            with open(log_path, "w", encoding="utf-8") as f:
                f.write(execution_output)

            return {
                "status": "success",
                "test_name": test_name,
                "timestamp": timestamp,
                "log_file": log_path,
                "screenshot": screenshot_path,
                "message": execution_output[:500]
            }

        except Exception as e:
            # Restaurar stdout si falló
            sys.stdout = original_stdout

            error_message = f"❌ Error durante ejecución:\n{str(e)}\n\n{traceback.format_exc()}"
            print(error_message)

            save_log(safe_test_name, error_message)

            # screenshot de error
            if self.driver:
                try:
                    save_screenshot(self.driver, f"{safe_test_name}_ERROR")
                except:
                    pass

            # log parcial
            execution_output = output_buffer.getvalue()

            with open(log_path, "w", encoding="utf-8") as f:
                f.write(execution_output)
                f.write("\n\n" + error_message)

            return {
                "status": "error",
                "test_name": test_name,
                "timestamp": timestamp,
                "log_file": log_path,
                "screenshot": screenshot_path,
                "message": error_message
            }

        finally:
            sys.stdout = original_stdout
            if self.driver:
                try:
                    print("🔄 Cerrando navegador...")
                    time.sleep(2)
                    self.driver.quit()
                    print("✅ Navegador cerrado correctamente")
                except Exception as e:
                    print(f"⚠️ Error al cerrar navegador: {e}")
