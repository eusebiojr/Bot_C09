#!/bin/bash
# setup_gcp.sh - Configuração inicial do Google Cloud Platform

# Configurações
PROJECT_ID="seu-projeto-id"  # ALTERE AQUI
REGION="southamerica-east1"
SERVICE_ACCOUNT="c09-bot"

echo "🚀 Configurando projeto GCP para Sistema C09..."

# 1. Define projeto ativo
gcloud config set project $PROJECT_ID

# 2. Habilita APIs necessárias
echo "📦 Habilitando APIs..."
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable scheduler.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable containerregistry.googleapis.com

# 3. Cria Service Account
echo "🔐 Criando Service Account..."
gcloud iam service-accounts create $SERVICE_ACCOUNT \
    --display-name="Sistema C09 Bot" \
    --description="Service Account para automação C09"

# 4. Adiciona permissões necessárias
echo "🛡️ Configurando permissões..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/run.invoker"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/logging.logWriter"

# 5. Cria secrets para credenciais
echo "🔑 Criando secrets..."

# Cria secrets (você precisará definir os valores depois)
gcloud secrets create frota-user --data-file=- <<< "PLACEHOLDER"
gcloud secrets create frota-password --data-file=- <<< "PLACEHOLDER" 
gcloud secrets create sp-user --data-file=- <<< "PLACEHOLDER"
gcloud secrets create sp-password --data-file=- <<< "PLACEHOLDER"

echo "✅ Secrets criados. Configure os valores reais com:"
echo "   gcloud secrets versions add frota-user --data-file=-"
echo "   gcloud secrets versions add frota-password --data-file=-"
echo "   gcloud secrets versions add sp-user --data-file=-"
echo "   gcloud secrets versions add sp-password --data-file=-"

# 6. Cria jobs do Cloud Scheduler (placeholder)
echo "⏰ Criando Cloud Scheduler jobs..."

# Job COMPLETO (a cada 1 hora)
gcloud scheduler jobs create http c09-completo \
    --location=$REGION \
    --schedule="0 * * * *" \
    --uri="https://c09-bot-completo-HASH-$REGION.a.run.app" \
    --http-method="POST" \
    --headers="Content-Type=application/json" \
    --message-body='{"mode": "COMPLETO"}' \
    --time-zone="America/Sao_Paulo"

# Job CANDLES (a cada 10 minutos)  
gcloud scheduler jobs create http c09-candles \
    --location=$REGION \
    --schedule="*/10 * * * *" \
    --uri="https://c09-bot-candles-HASH-$REGION.a.run.app" \
    --http-method="POST" \
    --headers="Content-Type=application/json" \
    --message-body='{"mode": "CANDLES"}' \
    --time-zone="America/Sao_Paulo"

echo "🎉 Configuração básica concluída!"
echo ""
echo "📋 PRÓXIMOS PASSOS:"
echo "1. Configure PROJECT_ID no cloudbuild.yaml"
echo "2. Configure as credenciais nos secrets"  
echo "3. Execute: gcloud builds submit --config cloudbuild.yaml"
echo "4. Atualize URLs dos jobs no Cloud Scheduler"