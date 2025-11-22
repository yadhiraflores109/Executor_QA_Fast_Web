import json
import os
from datetime import datetime
from typing import Dict, Any
from app.utils.file_utils import save_log

class Reporter:
    """
    Genera reportes detallados de cada ejecución del agente.
    Guarda la información en formato JSON.
    """
    def __init__(self, report_dir: str = "app/results/reports"):
        self.report_dir = report_dir
        os.makedirs(self.report_dir, exist_ok=True)

    def generate_report(
        self,
        result: Dict[str, Any],
        execution_time: float,
        steps: list = None
    ) -> Dict[str, Any]:
        """
        Genera y guarda un archivo JSON con los detalles de la ejecución.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_name = f"{result.get('test_name', 'test')}_{timestamp}.json"
        report_path = os.path.join(self.report_dir, report_name)

        report_data = {
            "test_name": result.get("test_name"),
            "status": result.get("status"),
            "timestamp": result.get("timestamp"),
            "execution_time": execution_time,
            "log_file": result.get("log_file"),
            "screenshot": result.get("screenshot", None),
            "message": result.get("message"),
            "steps_executed": steps if steps else [],
            "generated_at": timestamp
        }

        try:
            with open(report_path, "w", encoding="utf-8") as f:
                json.dump(report_data, f, indent=4, ensure_ascii=False)
            save_log(result.get("log_file"), f"Reporte generado: {report_path}")
        except Exception as e:
            save_log(result.get("log_file"), f"Error al generar reporte: {e}")

        return report_data

    def get_last_reports(self, limit: int = 5):
        """
        Devuelve los últimos reportes generados en formato JSON.
        """
        reports = []
        try:
            files = sorted(
                [f for f in os.listdir(self.report_dir) if f.endswith(".json")],
                key=lambda x: os.path.getmtime(os.path.join(self.report_dir, x)),
                reverse=True
            )
            for file in files[:limit]:
                with open(os.path.join(self.report_dir, file), "r", encoding="utf-8") as f:
                    reports.append(json.load(f))
        except Exception as e:
            print(f"Error al leer reportes: {e}")
        return reports
