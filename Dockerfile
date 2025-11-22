# --- Imagen base ---
FROM python:3.11-slim

# --- Variables de entorno ---
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DISPLAY=:99

# --- Instalar dependencias del sistema ---
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    curl \
    chromium \
    chromium-driver \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# --- Permisos necesarios para ChromeDriver ---
RUN chmod 755 /usr/lib/chromium/chromedriver

# --- Directorio de trabajo ---
WORKDIR /app

# --- Copiar dependencias ---
COPY requirements.txt .

# --- Instalar dependencias Python ---
RUN pip install --no-cache-dir -r requirements.txt

# --- Copiar código fuente ---
COPY app/ /app/app/

# --- Exponer puerto ---
EXPOSE 8081

# --- Comando de inicio ---
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8081"]
