# deploy.ps1 - Deploy Cloud Run via PowerShell

# ===== CONFIGURAÇÕES (AJUSTE AQUI) =====
$PROJECT_ID = "sz-wsp-00009"  # MUDE AQUI
$SERVICE_NAME = "c09-processor"
$REGION = "us-central1"          # ou southamerica-east1
$IMAGE_NAME = "gcr.io/$PROJECT_ID/$SERVICE_NAME"

# ===== CREDENCIAIS (AJUSTE AQUI) =====
$SP_USER = "eusebioagj@suzano.com.br"
$SP_PASSWORD = "290422@Cc"      # MUDE AQUI
$FROTA_USER = "Gabriela.Arraes" 
$FROTA_PASSWORD = "Gabizinha2896@"     # MUDE AQUI

Write-Host "🚀 DEPLOY SISTEMA C09 - CLOUD RUN" -ForegroundColor Green
Write-Host "==================================" -ForegroundColor Green
Write-Host "Projeto: $PROJECT_ID" -ForegroundColor Yellow
Write-Host "Serviço: $SERVICE_NAME" -ForegroundColor Yellow
Write-Host "Região: $REGION" -ForegroundColor Yellow
Write-Host ""

# 1. Configurar projeto
Write-Host "🔧 Configurando projeto..." -ForegroundColor Blue
gcloud config set project $PROJECT_ID
gcloud config set run/region $REGION

# 2. Habilitar APIs
Write-Host "📋 Habilitando APIs necessárias..." -ForegroundColor Blue
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable cloudscheduler.googleapis.com

# 3. Build da imagem
Write-Host "📦 Construindo imagem Docker..." -ForegroundColor Blue
gcloud builds submit --tag $IMAGE_NAME

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Erro no build da imagem!" -ForegroundColor Red
    exit 1
}

# 4. Deploy no Cloud Run
Write-Host "☁️ Fazendo deploy no Cloud Run..." -ForegroundColor Blue
gcloud run deploy $SERVICE_NAME `
    --image $IMAGE_NAME `
    --platform managed `
    --region $REGION `
    --allow-unauthenticated `
    --memory 4Gi `
    --cpu 2 `
    --timeout 900 `
    --max-instances 1 `
    --min-instances 0 `
    --concurrency 1 `
    --set-env-vars "K_SERVICE=true,SP_USER=$SP_USER,SP_PASSWORD=$SP_PASSWORD,FROTA_USER=$FROTA_USER,FROTA_PASSWORD=$FROTA_PASSWORD,PYTHONUNBUFFERED=1"

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Erro no deploy!" -ForegroundColor Red
    exit 1
}

# 5. Obter URL do serviço
Write-Host "🔍 Obtendo URL do serviço..." -ForegroundColor Blue
$SERVICE_URL = gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)"

Write-Host ""
Write-Host "✅ DEPLOY CONCLUÍDO!" -ForegroundColor Green
Write-Host "🌐 URL do serviço: $SERVICE_URL" -ForegroundColor Yellow

# 6. Teste inicial
Write-Host ""
Write-Host "🧪 Testando deployment..." -ForegroundColor Blue
try {
    $healthResponse = Invoke-RestMethod -Uri "$SERVICE_URL/health" -Method Get
    Write-Host "✅ Health check OK" -ForegroundColor Green
    
    $statusResponse = Invoke-RestMethod -Uri "$SERVICE_URL/status" -Method Get
    Write-Host "✅ Status check OK" -ForegroundColor Green
} catch {
    Write-Host "⚠️ Testes de conectividade falharam - verifique URL" -ForegroundColor Yellow
}

# 7. Configurar Cloud Scheduler
Write-Host ""
Write-Host "⏰ Configurando Cloud Scheduler..." -ForegroundColor Blue
gcloud scheduler jobs create http c09-scheduler-job `
    --schedule="*/10 * * * *" `
    --uri="$SERVICE_URL/trigger" `
    --http-method=POST `
    --timeout=900s `
    --location=$REGION `
    --description="Executa Sistema C09 a cada 10 minutos"

Write-Host ""
Write-Host "🎉 CONFIGURAÇÃO COMPLETA!" -ForegroundColor Green
Write-Host "==================================" -ForegroundColor Green
Write-Host "✅ Cloud Run deployado: $SERVICE_URL" -ForegroundColor Yellow
Write-Host "⏰ Scheduler configurado: execução a cada 10 minutos" -ForegroundColor Yellow
Write-Host "📊 Monitoramento: Cloud Console > Cloud Run > $SERVICE_NAME" -ForegroundColor Yellow
Write-Host ""
Write-Host "🔍 PRÓXIMOS PASSOS:" -ForegroundColor Cyan
Write-Host "1. Monitore primeira execução automática" -ForegroundColor White
Write-Host "2. Configure alertas no Cloud Monitoring" -ForegroundColor White
Write-Host "3. Teste manual: Invoke-RestMethod -Uri `"$SERVICE_URL/trigger`" -Method Post" -ForegroundColor White