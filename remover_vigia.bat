@echo off
chcp 65001 >nul
echo ============================================
echo  Delivery Control - Remover Vigia
echo ============================================
echo.
echo IMPORTANTE: execute como administrador
echo.
pause

schtasks /delete /tn "DeliveryControlWatchdog" /f

echo.
echo Vigia removido. O servico continua rodando
echo normalmente, so sem a checagem extra.
echo.
pause
