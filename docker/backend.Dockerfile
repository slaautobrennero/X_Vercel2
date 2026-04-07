# ============================================
# Backend Dockerfile - FastAPI
# ============================================
# 
# Build:
#   docker build -t sla-backend .
#
# Run standalone:
#   docker run -p 8001:8001 sla-backend
#
# ============================================

# Usa Python slim per immagine leggera
FROM python:3.11-slim

# Metadata
LABEL maintainer="SLA Sindacato"
LABEL description="Backend FastAPI per Portale Rimborsi SLA"

# Variabili ambiente
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Directory di lavoro
WORKDIR /app

# Installa dipendenze sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copia requirements e installa dipendenze Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia codice sorgente
COPY . .

# Crea directory uploads
RUN mkdir -p /app/uploads

# Esponi porta
EXPOSE 8001

# Comando di avvio
# Usa gunicorn in produzione per performance migliori
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8001"]

# Per produzione con gunicorn (decommentare):
# CMD ["gunicorn", "server:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8001"]
