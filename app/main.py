from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.executor import SeleniumExecutor
from app.reporter import Reporter
import traceback
import time

app = FastAPI(
    title="QA Agent Executor",
    description="Agente encargado de ejecutar scripts Selenium generados por Manus IA",
    version="1.0.0"
)

# Instancias globales
executor = SeleniumExecutor()
reporter = Reporter()


# Modelo de entrada del script
class ExecutionRequest(BaseModel):
    script: str             # Código Selenium generado dinámicamente
    test_name: str          # Nombre de la prueba (por ejemplo: login_test)
    browser: str = "chrome" # Navegador por defecto
    headless: bool = True   # Si se ejecuta sin interfaz visible


@app.post("/execute")
async def execute_script(request: ExecutionRequest):
    """
    Endpoint principal que recibe el script generado por el backend QA
    y lo ejecuta en el navegador.
    """
    start_time = time.time()

    try:
        # Ejecutar script en el navegador (controlado por Selenium)
        execution_result = executor.run_script(
            script=request.script,
            test_name=request.test_name,
            browser=request.browser,
            headless=request.headless
        )

        # Generar reporte con los resultados
        report_data = reporter.generate_report(
            result=execution_result,
            execution_time=time.time() - start_time
        )

        return {
            "status": "success",
            "message": "Ejecución completada correctamente",
            "data": report_data
        }

    except Exception as e:
        # En caso de fallo, registrar error y devolver respuesta controlada
        error_trace = traceback.format_exc()
        error_result = {
            "test_name": request.test_name,
            "status": "error",
            "timestamp": time.strftime("%Y%m%d_%H%M%S"),
            "log_file": f"app/results/logs/{request.test_name}.log",
            "message": str(e)
        }
        reporter.generate_report(error_result, time.time() - start_time)

        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "trace": error_trace
            }
        )


@app.get("/reports/latest")
async def get_latest_reports(limit: int = 5):
    """
    Devuelve los últimos reportes generados por el agente.
    """
    reports = reporter.get_last_reports(limit=limit)
    return {
        "status": "success",
        "total_reports": len(reports),
        "reports": reports
    }


@app.get("/")
def root():
    return {
        "message": " QA Agent Executor activo y listo para recibir scripts Selenium"
    }
