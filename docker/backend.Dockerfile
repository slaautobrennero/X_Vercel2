# ============================================
# Backend Dockerfile - FastAPI
# ============================================
# 
# Build:
#   docker build -t sla-backend -f backend.Dockerfile ../backend
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
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir emergentintegrations --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/ && \
    pip install --no-cache-dir -r requirements.txt

# Copia codice sorgente backend
COPY backend/ .

# Crea directory uploads
RUN mkdir -p /app/uploads && chmod 777 /app/uploads

# Esponi porta
EXPOSE 8001

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8001/api/health')" || exit 1

# Comando di avvio
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8001"]
