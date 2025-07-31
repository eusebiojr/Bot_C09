# Dockerfile Otimizado para Cloud Run + ChromeDriver
FROM python:3.11-slim

# Instala dependências do sistema para Chrome/Chromium
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libxkbcommon0 \
    libxss1 \
    libgconf-2-4 \
    && rm -rf /var/lib/apt/lists/*

# Adiciona repositório oficial do Google Chrome
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list

# Instala Google Chrome (versão estável)
RUN apt-get update && apt-get install -y \
    google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Verifica instalação do Chrome
RUN google-chrome --version

# Define diretório de trabalho
WORKDIR /app

# Copia requirements e instala dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia código da aplicação
COPY . .

# Cria diretórios necessários
RUN mkdir -p logs
RUN mkdir -p config

# Define variáveis de ambiente para Cloud Run
ENV K_SERVICE=true
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Configurações do Chrome para Cloud Run
ENV CHROME_BIN=/usr/bin/google-chrome
ENV DISPLAY=:99

# Configurações de memória
ENV PYTHONMALLOC=malloc

# Expõe porta (Cloud Run exige)
EXPOSE 8080

# Health check otimizado
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# CORRIGIDO: Executa app.py diretamente
CMD ["python", "app.py"]