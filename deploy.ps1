# deploy_clean.ps1 - Sistema C09 Bot (LIMPO)
# Execute: PowerShell -ExecutionPolicy Bypass -File .\deploy_clean.ps1

$PROJECT_ID = "sz-wsp-00009"
$SERVICE_COMPLETO = "c09-bot-completo"
$SERVICE_CANDLES = "c09-bot-candles"
$REGION = "us-central1"

Write-Host "Deploy Sistema C09 Bot" -ForegroundColor Green
Write-Host "=======================" -ForegroundColor Green
Write-Host "Projeto: $PROJECT_ID"
Write-Host "Regiao: $REGION"
Write-Host ""

# Configura projeto
Write-Host "Configurando projeto..." -ForegroundColor Yellow
gcloud config set project $PROJECT_ID

# Deploy COMPLETO
Write-Host "Fazendo deploy COMPLETO..." -ForegroundColor Yellow
gcloud run deploy $SERVICE_COMPLETO --source . --region $REGION --platform managed --allow-unauthenticated --memory 2Gi --cpu 1 --min-instances 0 --max-instances 1 --port 8080 --timeout 900 --set-env-vars EXECUTION_MODE=COMPLETO

if ($LASTEXITCODE -eq 0) {
    Write-Host "COMPLETO: Sucesso!" -ForegroundColor Green
    
    # Deploy CANDLES
    Write-Host "Fazendo deploy CANDLES..." -ForegroundColor Yellow
    gcloud run deploy $SERVICE_CANDLES --source . --region $REGION --platform managed --allow-unauthenticated --memory 1Gi --cpu 1 --min-instances 0 --max-instances 2 --port 8080 --timeout 300 --set-env-vars EXECUTION_MODE=CANDLES
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "SUCESSO TOTAL! Ambos servicos online!" -ForegroundColor Green
        Write-Host ""
        
        # Pega URLs
        $URL1 = gcloud run services describe $SERVICE_COMPLETO --region=$REGION --format="value(status.url)"
        $URL2 = gcloud run services describe $SERVICE_CANDLES --region=$REGION --format="value(status.url)"
        
        Write-Host "URLs dos servicos:" -ForegroundColor Cyan
        Write-Host "COMPLETO: $URL1"
        Write-Host "CANDLES:  $URL2"
        Write-Host ""
        Write-Host "Teste: Acesse $URL1 para verificar"
        
    } else {
        Write-Host "CANDLES falhou, mas COMPLETO funcionou" -ForegroundColor Yellow
    }
    
} else {
    Write-Host "COMPLETO falhou" -ForegroundColor Red
    Write-Host "Verifique os logs acima"
}

Write-Host ""
Write-Host "Deploy finalizado"