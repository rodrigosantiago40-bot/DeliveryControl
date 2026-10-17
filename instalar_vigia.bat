@echo off
chcp 65001 >nul
echo ============================================
echo  Delivery Control - Instalar Vigia (Watchdog)
echo ============================================
echo.
echo IMPORTANTE: feche este arquivo e execute-o
echo clicando com o botao direito e escolhendo
echo "Executar como administrador".
echo.
echo Pre-requisito: o servico DeliveryControlServidor
echo precisa ja estar instalado (rode antes o
echo instalar_servico.bat, se ainda nao rodou).
echo.
pause

set PASTA=C:\Projetos\DeliveryControl
set PYTHON=%PASTA%\venv\Scripts\pythonw.exe
set SCRIPT=%PASTA%\watchdog_servidor.py
set TAREFA=DeliveryControlWatchdog

echo Removendo tarefa antiga (se existir)...
schtasks /delete /tn "%TAREFA%" /f >nul 2>&1

echo Criando a tarefa agendada (verifica a cada 3 minutos, sempre)...
schtasks /create /tn "%TAREFA%" /tr "\"%PYTHON%\" \"%SCRIPT%\"" /sc minute /mo 3 /ru SYSTEM /rl HIGHEST /f

echo.
echo ============================================
echo  Pronto! A partir de agora, a cada 3 minutos
echo  o sistema confere se o site esta respondendo.
echo  Se nao estiver, reinicia o servico sozinho.
echo ============================================
echo.
echo Historico de reinicios forcados fica salvo em:
echo %PASTA%\watchdog_log.txt
echo.
pause
