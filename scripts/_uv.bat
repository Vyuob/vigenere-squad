@echo off
rem Trouve uv, ou l'installe (outil officiel astral.sh). Laisse le PATH mis a jour pour le script appelant.
where uv >nul 2>&1
if not errorlevel 1 exit /b 0
if exist "%USERPROFILE%\.local\bin\uv.exe" set "PATH=%USERPROFILE%\.local\bin;%PATH%"
where uv >nul 2>&1
if not errorlevel 1 exit /b 0
echo uv est introuvable : installation de uv...
powershell -NoProfile -ExecutionPolicy Bypass -Command "irm https://astral.sh/uv/install.ps1 | iex"
set "PATH=%USERPROFILE%\.local\bin;%PATH%"
where uv >nul 2>&1
if not errorlevel 1 exit /b 0
echo ERREUR : uv n'a pas pu etre installe. Voir https://docs.astral.sh/uv/getting-started/installation/
exit /b 1
