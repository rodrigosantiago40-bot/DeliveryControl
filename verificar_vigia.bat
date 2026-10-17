@echo off
chcp 65001 >nul
echo ============================================
echo  Delivery Control - Status do Vigia
echo ============================================
echo.
schtasks /query /tn "DeliveryControlWatchdog" /v /fo LIST | findstr /i "TaskName Status "Ultima Execu" "Proxima Execu" "Last Run" "Next Run""
echo.
echo --- Ultimas linhas do log do vigia ---
if exist "C:\Projetos\DeliveryControl\watchdog_log.txt" (
    powershell -command "Get-Content 'C:\Projetos\DeliveryControl\watchdog_log.txt' -Tail 10"
) else (
    echo Nenhum reinicio forcado registrado ainda - bom sinal!
)
echo.
pause
