@echo off
setlocal
cd /d "%~dp0"
call "%~dp0scripts\_uv.bat"
if errorlevel 1 goto erreur
uv sync --frozen
if errorlevel 1 goto erreur
echo Demonstration locale sur http://127.0.0.1:8765  (Ctrl+C pour arreter)
start "" cmd /c "timeout /t 3 >nul & start http://127.0.0.1:8765"
uv run --frozen vigenere-squad demo
exit /b 0
:erreur
echo ECHEC. Lancez d'abord installer.bat.
pause
exit /b 1
