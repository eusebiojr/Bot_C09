@echo off
chcp 65001 >nul
echo 🚀 CONFIGURAÇÃO SISTEMA C09 - CLOUD RUN
echo ==========================================

REM Verifica se gcloud está instalado
gcloud --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Google Cloud CLI não instalado!
    echo 📥 Baixe em: https://cloud.google.com/sdk/docs/install
    pause
    exit /b 1
)

REM Obtém ID do projeto atual
for /f "tokens=2" %%i in ('gcloud config get-value project 2^>nul') do set PROJECT_ID=%%i
if "%PROJECT_ID%"=="" (
    echo ❌ Projeto GCP não configurado!
    echo 💡 Execute: gcloud config set project SEU-PROJETO-ID
    pause
    exit /b 1
)

echo ✅ Projeto configurado: %PROJECT_ID%
echo.

echo 📦 Habilitando APIs necessárias...
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com  
gcloud services enable scheduler.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable containerregistry.googleapis.com

if %errorlevel% neq 0 (
    echo ❌ Erro ao habilitar APIs
    pause
    exit /b 1
)

echo ✅ APIs habilitadas com sucesso
echo.

echo 🔐 Criando Service Account...
gcloud iam service-accounts create c09-bot --display-name="Sistema C09 Bot" --description="Service Account para automação C09" 2>nul

echo 🛡️ Configurando permissões...
gcloud projects add-iam-policy-binding %PROJECT_ID% --member="serviceAccount:c09-bot@%PROJECT_ID%.iam.gserviceaccount.com" --role="roles/run.invoker" >nul
gcloud projects add-iam-policy-binding %PROJECT_ID% --member="serviceAccount:c09-bot@%PROJECT_ID%.iam.gserviceaccount.com" --role="roles/secretmanager.secretAccessor" >nul  
gcloud projects add-iam-policy-binding %PROJECT_ID% --member="serviceAccount:c09-bot@%PROJECT_ID%.iam.gserviceaccount.com" --role="roles/logging.logWriter" >nul

echo ✅ Permissões configuradas
echo.

echo 🔑 Configurando credenciais...
echo.
echo ⚠️  ATENÇÃO: Você precisará inserir as credenciais reais
echo.

REM Frota User
set /p FROTA_USER="Digite o usuário Frotalog (ex: Gabriela.Arraes): "
echo %FROTA_USER% | gcloud secrets create frota-user --data-file=- 2>nul
if %errorlevel% neq 0 (
    echo %FROTA_USER% | gcloud secrets versions add frota-user --data-file=- >nul
)

REM Frota Password  
set /p FROTA_PASSWORD="Digite a senha Frotalog: "
echo %FROTA_PASSWORD% | gcloud secrets create frota-password --data-file=- 2>nul
if %errorlevel% neq 0 (
    echo %FROTA_PASSWORD% | gcloud secrets versions add frota-password --data-file=- >nul
)

REM SP User
set /p SP_USER="Digite o usuário SharePoint (ex: eusebioagj@suzano.com.br): "
echo %SP_USER% | gcloud secrets create sp-user --data-file=- 2>nul
if %errorlevel% neq 0 (
    echo %SP_USER% | gcloud secrets versions add sp-user --data-file=- >nul
)

REM SP Password
set /p SP_PASSWORD="Digite a senha SharePoint: "
echo %SP_PASSWORD% | gcloud secrets create sp-password --data-file=- 2>nul
if %errorlevel% neq 0 (
    echo %SP_PASSWORD% | gcloud secrets versions add sp-password --data-file=- >nul
)

echo ✅ Credenciais configuradas nos Google Secrets
echo.

echo 🎉 CONFIGURAÇÃO CONCLUÍDA COM SUCESSO!
echo.
echo 📋 PRÓXIMOS PASSOS:
echo 1. Execute: gcloud builds submit --config cloudbuild.yaml
echo 2. Aguarde o build completar (5-10 minutos)
echo 3. Configure Cloud Scheduler
echo.
echo 💰 Custo estimado: R$ 150-200/mês
echo.
pause