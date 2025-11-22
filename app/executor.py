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
    def __init__(self, headless: bool = False):
        self.headless = headless
        self.driver = None

    def _init_driver(self):
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless=new")
        else:
            # ✅ ASEGURAR QUE EL NAVEGADOR SE MUESTRE
            chrome_options.add_argument("--start-maximized")
        
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # ✅ Deshabilitar notificaciones molestas
        chrome_options.add_experimental_option("prefs", {
            "profile.default_content_setting_values.notifications": 2
        })

        try:
            from webdriver_manager.chrome import ChromeDriverManager
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            print(f"✅ Navegador Chrome iniciado (headless={self.headless})")
        except Exception as e:
            raise RuntimeError(f"❌ Error al inicializar el navegador: {e}")

    def run_script(self, script: str, test_name: str, browser: str = "chrome", headless: bool = False):
        self.headless = headless
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        os.makedirs("app/results/logs", exist_ok=True)
        os.makedirs("app/results/screenshots", exist_ok=True)
        
        log_path = f"app/results/logs/{test_name}_{timestamp}.log"
        screenshot_path = f"app/results/screenshots/{test_name}_{timestamp}.png"

        # ✅ Capturar prints del script usando StringIO
        output_buffer = io.StringIO()
        original_stdout = sys.stdout

        try:
            print(f"🚀 Iniciando ejecución de: {test_name}")
            self._init_driver()
            save_log(test_name, f"=== Inicio: {test_name} ===")

            # ✅ Redirigir stdout ANTES de ejecutar el script
            sys.stdout = output_buffer
            
            # ✅ Definir entorno de ejecución con TODAS las variables necesarias
            exec_env = {
                "__builtins__": __builtins__,  # Importante: incluir builtins
                "driver": self.driver,
                "By": By,
                "Keys": Keys,
                "WebDriverWait": WebDriverWait,
                "EC": EC,
                "time": time,
                "save_screenshot": lambda: save_screenshot(self.driver, test_name),
                # Agregar otras importaciones comunes que Manus podría usar
                "datetime": datetime,
                "os": os
            }

            print(f"📝 Ejecutando script generado por Manus...")
            print("=" * 80)
            
            # ✅ Ejecutar el script
            exec(script, exec_env)
            
            print("=" * 80)
            print(f"✅ Script completado")

            # ✅ Restaurar stdout ANTES de hacer otras operaciones
            sys.stdout = original_stdout

            # Capturar screenshot final
            save_screenshot(self.driver, test_name)
            save_log(test_name, "✅ Ejecución completada")

            # Obtener todo el output capturado
            execution_output = output_buffer.getvalue()
            
            # Guardar output en el log
            with open(log_path, 'w', encoding='utf-8') as f:
                f.write(execution_output)

            print(f"✅ Test completado: {test_name}")
            print(f"📄 Log guardado: {log_path}")
            print(f"📸 Screenshot: {screenshot_path}")

            result = {
                "status": "success",
                "test_name": test_name,
                "timestamp": timestamp,
                "log_file": log_path,
                "screenshot": screenshot_path,
                "message": f"✅ Test ejecutado exitosamente\n\nOutput capturado ({len(execution_output)} chars):\n{execution_output}"
            }

        except Exception as e:
            # ✅ Restaurar stdout en caso de error
            sys.stdout = original_stdout
            
            error_message = f"❌ Error durante ejecución:\n{str(e)}\n\n{traceback.format_exc()}"
            print(error_message)
            save_log(test_name, error_message)
            
            # Capturar screenshot del error
            if self.driver:
                try:
                    save_screenshot(self.driver, test_name + "_ERROR")
                except:
                    pass
            
            # Obtener output parcial antes del error
            execution_output = output_buffer.getvalue()
            
            # Guardar output parcial
            with open(log_path, 'w', encoding='utf-8') as f:
                f.write(execution_output)
                f.write("\n\n" + error_message)
            
            result = {
                "status": "error",
                "test_name": test_name,
                "timestamp": timestamp,
                "log_file": log_path,
                "screenshot": screenshot_path,
                "message": f"{error_message}\n\nOutput antes del error:\n{execution_output}"
            }

        finally:
            # ✅ Asegurar que stdout siempre se restaure
            sys.stdout = original_stdout
            
            if self.driver:
                print("🔄 Cerrando navegador...")
                time.sleep(2)
                self.driver.quit()
                print("✅ Navegador cerrado")

        return result