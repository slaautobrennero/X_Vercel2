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
COPY package.json yarn.lock ./

# Installa dipendenze
RUN yarn install --frozen-lockfile

# Copia sorgenti
COPY . .

# Build produzione
RUN yarn build

# Stage 2: Nginx per servire i file statici
FROM nginx:alpine

# Copia build React
COPY --from=builder /app/build /usr/share/nginx/html

# Copia configurazione Nginx personalizzata
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Esponi porta 80
EXPOSE 80

# Nginx in foreground
CMD ["nginx", "-g", "daemon off;"]
