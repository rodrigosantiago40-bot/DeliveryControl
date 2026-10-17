@echo off
chcp 65001 >nul
echo ============================================
echo  Delivery Control - Instalar Servico
echo ============================================
echo.
echo IMPORTANTE: feche este arquivo e execute-o
echo clicando com o botao direito e escolhendo
echo "Executar como administrador" - instalar um
echo servico do Windows exige essa permissao.
echo.
pause

set NOME_SERVICO=DeliveryControlServidor
set PASTA=C:\Projetos\DeliveryControl
set PYTHON=%PASTA%\venv\Scripts\python.exe
set SCRIPT=%PASTA%\app.py

echo.
echo Parando qualquer servidor antigo que esteja rodando...
taskkill /F /IM pythonw.exe /T >nul 2>&1
taskkill /F /IM python.exe /T >nul 2>&1

echo Instalando o servico "%NOME_SERVICO%"...
"%PASTA%\nssm.exe" install %NOME_SERVICO% "%PYTHON%" "%SCRIPT%"

echo Configurando pasta de trabalho...
"%PASTA%\nssm.exe" set %NOME_SERVICO% AppDirectory "%PASTA%"

echo Configurando nome e descricao...
"%PASTA%\nssm.exe" set %NOME_SERVICO% DisplayName "Delivery Control - Servidor Web"
"%PASTA%\nssm.exe" set %NOME_SERVICO% Description "Servidor web do sistema Delivery Control (lancamento de pedidos pelo navegador/celular)"

echo Configurando inicio automatico com o Windows...
"%PASTA%\nssm.exe" set %NOME_SERVICO% Start SERVICE_AUTO_START

echo Configurando reinicio automatico em caso de travamento/erro...
"%PASTA%\nssm.exe" set %NOME_SERVICO% AppExit Default Restart
"%PASTA%\nssm.exe" set %NOME_SERVICO% AppRestartDelay 3000

echo Configurando os arquivos de log (para investigar problemas depois)...
"%PASTA%\nssm.exe" set %NOME_SERVICO% AppStdout "%PASTA%\log_out.txt"
"%PASTA%\nssm.exe" set %NOME_SERVICO% AppStderr "%PASTA%\log_err.txt"
"%PASTA%\nssm.exe" set %NOME_SERVICO% AppRotateFiles 1
"%PASTA%\nssm.exe" set %NOME_SERVICO% AppRotateBytes 1048576

echo.
echo Iniciando o servico agora...
"%PASTA%\nssm.exe" start %NOME_SERVICO%

echo.
echo ============================================
echo  Pronto! O servidor agora:
echo  - liga sozinho com o Windows
echo  - reinicia sozinho se travar ou fechar
echo ============================================
echo.
echo Voce pode testar acessando pelo navegador
echo normalmente, do mesmo jeito que ja fazia.
echo.
pause
