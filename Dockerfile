# --- Etapa base ---
FROM python:3.11-slim

# --- Variables de entorno ---
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# --- Instalar dependencias del sistema ---
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    curl \
    chromium-driver \
    chromium \
    firefox-esr \
    && rm -rf /var/lib/apt/lists/*

# --- Crear directorios de trabajo ---
WORKDIR /app

# --- Copiar dependencias ---
COPY requirements.txt .

# --- Instalar dependencias Python ---
RUN pip install --no-cache-dir -r requirements.txt

# --- Copiar código fuente ---
COPY app/ /app/app/

# --- Exponer el puerto del servicio ---
EXPOSE 8081

# --- Comando de inicio ---
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8081"]
