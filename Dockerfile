# Dockerfile para Cloud Run
FROM python:3.11-slim

# Instala dependências do sistema necessárias para Chrome
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# Adiciona repositório do Google Chrome
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list

# Instala Google Chrome
RUN apt-get update && apt-get install -y \
    google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Define diretório de trabalho
WORKDIR /app

# Copia requirements e instala dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia código da aplicação
COPY . .

# Cria diretórios necessários
RUN mkdir -p logs

# Define variável de ambiente para Cloud Run
ENV K_SERVICE=true
ENV PYTHONPATH=/app

# Expõe porta (Cloud Run exige)
EXPOSE 8080

# Comando para executar aplicação
# Note: Cloud Run executará via Cloud Scheduler, não diretamente
CMD ["python", "main.py"]