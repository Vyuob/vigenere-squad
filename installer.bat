@echo off
setlocal
cd /d "%~dp0"
echo === Vigenere-Squad : installation ===
call "%~dp0scripts\_uv.bat"
if errorlevel 1 goto erreur
echo.
echo [1/2] Environnement fige (uv.lock)...
uv sync --frozen --extra dev
if errorlevel 1 goto erreur
echo.
echo [2/2] Tests (sans LLM)...
uv run --frozen pytest -q
if errorlevel 1 goto erreur
echo.
echo OK : installation terminee. Lancez demo.bat (demonstration) ou verifier.bat (integrite).
pause
exit /b 0
:erreur
echo.
echo ECHEC de l'installation. Voir les messages ci-dessus.
pause
exit /b 1
