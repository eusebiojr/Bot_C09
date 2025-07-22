@echo off
chcp 65001
 
REM Caminho fixo da pasta onde está o script
cd /d "C:\Users\tallespaiva\OneDrive - Suzano S A\Documentos\Bot_C09"
 
REM Checa se existe a pasta, se não, mostra erro e sai
if not exist "C:\Users\tallespaiva\OneDrive - Suzano S A\Documentos\Bot_C09" (
    echo Pasta de códigos não encontrada! Confira o caminho no .bat.
    timeout /t 10
    exit /b
)
 
:loop
REM Tenta rodar com Python do PATH
python C09_unificado.py
 
REM Se preferir, descomente a linha abaixo e comente a de cima, caso queira usar o caminho completo do Python:
REM "C:\Users\tallespaiva\AppData\Local\Programs\Python\Python313\python.exe" C09_unificado.py
 
REM Aguarda 10 minutos (600 segundos) antes de rodar de novo
timeout /t 600 /nobreak >nul
goto loop