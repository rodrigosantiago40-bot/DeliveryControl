@echo off
chcp 65001 >nul
echo ============================================
echo  Delivery Control - Status do Servico
echo ============================================
echo.
sc query DeliveryControlServidor
echo.
echo Se aparecer "RUNNING" acima, o servidor esta
echo funcionando normalmente.
echo.
pause
