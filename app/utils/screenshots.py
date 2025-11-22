import os
import time

SCREENSHOTS_DIR = "app/results/screenshots"
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

def take_screenshot(driver, test_name: str) -> str:
    """
    Captura una imagen de pantalla del estado actual del navegador.
    Retorna la ruta donde fue guardada.
    """
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"{test_name}_{timestamp}.png"
    filepath = os.path.join(SCREENSHOTS_DIR, filename)

    try:
        driver.save_screenshot(filepath)
        return filepath
    except Exception as e:
        print(f"Error al capturar pantalla: {e}")
        return None


# -------------------------------------------------------
# NUEVO: función requerida por executor.py
# -------------------------------------------------------
def save_screenshot(driver, test_name: str) -> str:
    """
    Alias compatible con lo que espera executor.py.
    Simplemente reutiliza take_screenshot().
    """
    return take_screenshot(driver, test_name)

