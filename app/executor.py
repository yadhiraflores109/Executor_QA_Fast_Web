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
        self.headless = headless
        self.driver = None

    def _init_driver(self):
        """Inicializa Chrome correctamente tanto para Docker como local."""

        chrome_options = Options()

        # HEADLESS correcto (Render NO soporta headless=new)
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-software-rasterizer")
        chrome_options.add_argument("--disable-extensions")

        # 🔥 RUTAS CORRECTAS PARA DOCKER + Render
        chrome_binary = "/usr/bin/chromium"
        chromedriver_path = "/usr/lib/chromium/chromedriver"

        if not os.path.exists(chrome_binary):
            raise FileNotFoundError(f"Chrome no encontrado: {chrome_binary}")

        if not os.path.exists(chromedriver_path):
            raise FileNotFoundError(f"ChromeDriver no encontrado: {chromedriver_path}")

        chrome_options.binary_location = chrome_binary
        service = Service(chromedriver_path)

        # Inicia el navegador
        self.driver = webdriver.Chrome(service=service, options=chrome_options)

        self.driver.set_page_load_timeout(30)
        self.driver.implicitly_wait(5)

        print("🚀 Chrome iniciado correctamente en modo headless en Render/Docker.")

    def run_script(self, script: str, test_name: str, browser: str = "chrome", headless: bool = True):

        self.headless = headless
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Crear carpetas si no existen
        os.makedirs("app/results/logs", exist_ok=True)
        os.makedirs("app/results/screenshots", exist_ok=True)

        safe_test_name = (
            test_name.replace(" ", "_")
                     .replace("/", "-")
                     .replace("\\", "-")
        )[:100]

        log_path = f"app/results/logs/{safe_test_name}_{timestamp}.log"

        # Redirigir consola temporalmente
        output_buffer = io.StringIO()
        original_stdout = sys.stdout

        try:
            print(f"Ejecutando test: {test_name}")

            self._init_driver()

            save_log(safe_test_name, f"=== Inicio ejecución del test {test_name} ===\n")

            # Redirigir stdout
            sys.stdout = output_buffer

            # Entorno seguro del exec
            exec_env = {
                "__builtins__": __builtins__,
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

            print("📝 Ejecutando script…")
            exec(script, exec_env)

            # Restaurar stdout
            sys.stdout = original_stdout

            # Screenshot final
            save_screenshot(self.driver, safe_test_name)
            save_log(safe_test_name, "Test ejecutado correctamente.")

            output = output_buffer.getvalue()

            # Guardar log
            with open(log_path, "w", encoding="utf-8") as f:
                f.write(output)

            return {
                "status": "success",
                "test_name": test_name,
                "log_file": log_path,
                "message": output[:500]
            }

        except Exception as e:
            sys.stdout = original_stdout

            error_message = f"❌ ERROR DURANTE EJECUCIÓN:\n{str(e)}\n{traceback.format_exc()}"
            print(error_message)

            save_log(safe_test_name, error_message)

            try:
                save_screenshot(self.driver, f"{safe_test_name}_ERROR")
            except:
                pass

            # Guardar log completo
            output = output_buffer.getvalue()
            with open(log_path, "w", encoding="utf-8") as f:
                f.write(output)
                f.write("\n\n" + error_message)

            return {
                "status": "error",
                "test_name": test_name,
                "log_file": log_path,
                "message": error_message
            }

        finally:
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
