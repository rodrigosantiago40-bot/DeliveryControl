@echo off
chcp 65001 >nul
echo ============================================
echo  Delivery Control - Reiniciar Servico
echo ============================================
echo.
echo IMPORTANTE: execute como administrador
echo.
pause

echo Reiniciando o servico...
C:\Projetos\DeliveryControl\nssm.exe restart DeliveryControlServidor

echo.
echo Pronto! Servico reiniciado.
echo.
pause
