@echo off
setlocal
cd /d "%~dp0"
echo === Vigenere-Squad : reproduction complete ===
echo.
echo ATTENTION : plusieurs heures sur un PC sans GPU (qwen3:4b et llama3.2:3b).
echo Ce script ECRASE results\, data\corpus_eval.jsonl et site\ avec les nouveaux resultats.
echo Pour revenir aux resultats livres ensuite : git restore .
echo.
choice /c ON /m "Continuer (O/N) ? "
if errorlevel 2 exit /b 0
call "%~dp0scripts\_uv.bat"
if errorlevel 1 goto erreur
where ollama >nul 2>&1
if errorlevel 1 (
  echo ERREUR : Ollama est introuvable. Installez-le depuis https://ollama.com/download puis relancez.
  goto erreur
)
uv sync --frozen --extra dev
if errorlevel 1 goto erreur
echo Mise en veille desactivee pendant la reproduction.
powercfg /change standby-timeout-ac 0
uv run --frozen python scripts/reproduce.py 
set CODE=%errorlevel%
powercfg /change standby-timeout-ac 30
echo Mise en veille remise a 30 minutes.
if not "%CODE%"=="0" goto erreur
echo.
echo OK : reproduction terminee. Resultats : results\metrics.json, site\index.html
pause
exit /b 0
:erreur
echo.
echo ECHEC. Voir les messages ci-dessus.
pause
exit /b 1
