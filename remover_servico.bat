@echo off
chcp 65001 >nul
echo ============================================
echo  Delivery Control - Remover Servico
echo ============================================
echo.
echo IMPORTANTE: execute como administrador
echo (botao direito - Executar como administrador)
echo.
pause

set NOME_SERVICO=DeliveryControlServidor
set PASTA=C:\Projetos\DeliveryControl

echo Parando o servico...
"%PASTA%\nssm.exe" stop %NOME_SERVICO%

echo Removendo o servico...
"%PASTA%\nssm.exe" remove %NOME_SERVICO% confirm

echo.
echo Servico removido. O sistema volta a precisar
echo do iniciar_servidor.vbs manualmente, como antes.
echo.
pause
