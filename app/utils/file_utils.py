import os
import time

LOGS_DIR = "app/results/logs"
os.makedirs(LOGS_DIR, exist_ok=True)

def save_log(test_name: str, message: str) -> str:
    """
    Guarda un mensaje en un archivo .log dentro de app/results/logs
    Devuelve la ruta del archivo.
    """
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"{test_name}_{timestamp}.log"
    filepath = os.path.join(LOGS_DIR, filename)

    try:
        with open(filepath, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {message}\n")
        return filepath
    except Exception as e:
        print(f"Error al guardar log: {e}")
        return None
