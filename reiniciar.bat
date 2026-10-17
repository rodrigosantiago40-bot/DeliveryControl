@echo off
taskkill /F /IM python.exe /T 2>nul
taskkill /F /IM pythonw.exe /T 2>nul
timeout /t 2 /nobreak >nul
start wscript.exe iniciar_servidor.vbs
echo Servidor reiniciado com sucesso!