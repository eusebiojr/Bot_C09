# deploy-final.sh - Deploy completo para Cloud Run

#!/bin/bash
set -e

# ===== CONFIGURAÇÕES (AJUSTE AQUI) =====
PROJECT_ID="sz-wsp-00009"  # MUDE AQUI
SERVICE_NAME="c09-processor"
REGION="us-central1"          # ou southamerica-east1
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"

# ===== CREDENCIAIS (AJUSTE AQUI) =====
SP_USER="eusebioagj@suzano.com.br"
SP_PASSWORD="SUA_SENHA_SHAREPOINT"      # MUDE AQUI
FROTA_USER="eusebio.suz" 
FROTA_PASSWORD="SUA_SENHA_FROTALOG"     # MUDE AQUI

echo "🚀 DEPLOY SISTEMA C09 - CLOUD RUN"
echo "=================================="
echo "Projeto: $PROJECT_ID"
echo "Serviço: $SERVICE_NAME"
echo "Região: $REGION"
echo ""

# 1. Configurar projeto
echo "🔧 Configurando projeto..."
gcloud config set project $PROJECT_ID
gcloud config set run/region $REGION

# 2. Build da imagem
echo "📦 Construindo imagem Docker..."
gcloud builds submit --tag $IMAGE_NAME

# 3. Deploy no Cloud Run
echo "☁️ Fazendo deploy no Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --image $IMAGE_NAME \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --memory 4Gi \
    --cpu 2 \
    --timeout 900 \
    --max-instances 1 \
    --min-instances 0 \
    --concurrency 1 \
    --set-env-vars "K_SERVICE=true" \
    --set-env-vars "SP_USER=$SP_USER" \
    --set-env-vars "SP_PASSWORD=$SP_PASSWORD" \
    --set-env-vars "FROTA_USER=$FROTA_USER" \
    --set-env-vars "FROTA_PASSWORD=$FROTA_PASSWORD" \
    --set-env-vars "PYTHONUNBUFFERED=1"

# 4. Obter URL do serviço
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)")
echo ""
echo "✅ DEPLOY CONCLUÍDO!"
echo "🌐 URL do serviço: $SERVICE_URL"

# 5. Teste inicial
echo ""
echo "🧪 Testando deployment..."
curl -f "$SERVICE_URL/health" && echo " - Health check OK"
curl -f "$SERVICE_URL/status" && echo " - Status check OK"

# 6. Configurar Cloud Scheduler
echo ""
echo "⏰ Configurando Cloud Scheduler..."
gcloud scheduler jobs create http c09-scheduler-job \
    --schedule="*/10 * * * *" \
    --uri="$SERVICE_URL/trigger" \
    --http-method=POST \
    --timeout=900s \
    --location=$REGION \
    --description="Executa Sistema C09 a cada 10 minutos"

echo ""
echo "🎉 CONFIGURAÇÃO COMPLETA!"
echo "=================================="
echo "✅ Cloud Run deployado: $SERVICE_URL"
echo "⏰ Scheduler configurado: execução a cada 10 minutos"
echo "📊 Monitoramento: Cloud Console > Cloud Run > $SERVICE_NAME"
echo "📋 Logs: gcloud logging read 'resource.type=cloud_run_revision'"
echo ""
echo "🔍 PRÓXIMOS PASSOS:"
echo "1. Monitore primeira execução automática"
echo "2. Configure alertas no Cloud Monitoring"
echo "3. Teste manual: curl -X POST $SERVICE_URL/trigger"