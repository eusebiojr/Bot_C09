# deploy.sh - Script de Deploy para Cloud Run

#!/bin/bash
set -e

# Configurações
PROJECT_ID="sz-wsp-00009"
SERVICE_NAME="c09-processor"
REGION="us-central1"
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"

echo "🚀 Iniciando deploy Cloud Run..."

# 1. Build da imagem
echo "📦 Construindo imagem Docker..."
docker build -t $IMAGE_NAME .

# 2. Push para Google Container Registry
echo "☁️ Enviando para Google Container Registry..."
docker push $IMAGE_NAME

# 3. Deploy no Cloud Run
echo "🌐 Fazendo deploy no Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --image $IMAGE_NAME \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --memory 4Gi \
    --cpu 2 \
    --timeout 900 \
    --max-instances 1 \
    --set-env-vars "K_SERVICE=true" \
    --set-env-vars "SP_USER=eusebioagj@suzano.com.br" \
    --set-env-vars "SP_PASSWORD=SEU_PASSWORD_AQUI" \
    --set-env-vars "FROTA_USER=eusebio.suz" \
    --set-env-vars "FROTA_PASSWORD=SEU_PASSWORD_AQUI"

# 4. Obter URL do serviço
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)")
echo "✅ Serviço deployado: $SERVICE_URL"

# 5. Configurar Cloud Scheduler
echo "⏰ Configurando Cloud Scheduler..."
gcloud scheduler jobs create http c09-scheduler-job \
    --schedule="*/10 * * * *" \
    --uri="$SERVICE_URL/trigger" \
    --http-method=POST \
    --location=$REGION

echo "🎉 Deploy concluído!"
echo "📊 URL do serviço: $SERVICE_URL"
echo "⚡ Scheduler configurado para executar a cada 10 minutos"

# setup-project.sh - Configuração inicial do projeto GCP

#!/bin/bash

# Configurações
PROJECT_ID="seu-projeto-gcp"
REGION="us-central1"

echo "🔧 Configurando projeto GCP..."

# 1. Definir projeto
gcloud config set project $PROJECT_ID

# 2. Habilitar APIs necessárias
echo "📋 Habilitando APIs..."
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable cloudscheduler.googleapis.com
gcloud services enable logging.googleapis.com

# 3. Configurar região padrão
gcloud config set run/region $REGION

echo "✅ Projeto configurado!"

# test-local.sh - Teste local antes do deploy

#!/bin/bash

echo "🧪 Testando aplicação localmente..."

# 1. Exportar variáveis de ambiente
export K_SERVICE=false
export PORT=8080

# 2. Instalar dependências
pip install -r requirements.txt

# 3. Executar app.py
python app.py &
APP_PID=$!

# 4. Aguardar inicialização
sleep 5

# 5. Testar endpoints
echo "🔍 Testando health check..."
curl -f http://localhost:8080/health || echo "❌ Health check falhou"

echo "🔍 Testando status..."
curl -f http://localhost:8080/status || echo "❌ Status falhou"

# 6. Finalizar processo
kill $APP_PID

echo "✅ Testes locais concluídos!"

# monitor.sh - Script de monitoramento

#!/bin/bash

SERVICE_NAME="c09-processor"
REGION="us-central1"

echo "📊 Monitoramento Cloud Run..."

# 1. Status do serviço
echo "🔍 Status do serviço:"
gcloud run services describe $SERVICE_NAME --region=$REGION

# 2. Logs recentes
echo "📋 Logs das últimas 2 horas:"
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME" \
    --limit=50 \
    --format="table(timestamp,severity,textPayload)" \
    --freshness=2h

# 3. Estatísticas de execução
echo "📈 Estatísticas do Scheduler:"
gcloud scheduler jobs describe c09-scheduler-job --location=$REGION