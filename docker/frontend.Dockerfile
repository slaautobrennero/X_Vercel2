# ============================================
# Frontend Dockerfile - React + Nginx
# ============================================
# 
# Build multi-stage:
# 1. Build React app
# 2. Serve con Nginx
#
# Build:
#   docker build -t sla-frontend --build-arg REACT_APP_BACKEND_URL=http://api.tuodominio.it .
#
# ============================================

# Stage 1: Build React
FROM node:18-alpine AS builder

WORKDIR /app

# Argomento per URL backend
ARG REACT_APP_BACKEND_URL=http://localhost:8001
ENV REACT_APP_BACKEND_URL=$REACT_APP_BACKEND_URL

# Copia package files
COPY frontend/package.json frontend/yarn.lock ./

# Installa dipendenze con legacy peer deps (fix date-fns conflict)
RUN yarn install --frozen-lockfile --legacy-peer-deps

# Copia sorgenti frontend
COPY frontend/ .

# Build produzione
RUN yarn build

# Stage 2: Nginx per servire i file statici
FROM nginx:alpine

# Metadata
LABEL maintainer="SLA Sindacato"
LABEL description="Frontend React per Portale Rimborsi SLA"

# Copia build React
COPY --from=builder /app/build /usr/share/nginx/html

# Copia configurazione Nginx personalizzata
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf

# Esponi porta 80
EXPOSE 80

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD wget --quiet --tries=1 --spider http://localhost/health || exit 1

# Nginx in foreground
CMD ["nginx", "-g", "daemon off;"]
