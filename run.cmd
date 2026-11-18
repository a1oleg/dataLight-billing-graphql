@echo off
setlocal
cd /d "%~dp0"

set "PYTHON=%DSH_PYTHON%"
if defined PYTHON goto have_python

set "BUNDLED=C:\Users\a1ole\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe"
if exist "%BUNDLED%" (
  set "PYTHON=%BUNDLED%"
  goto have_python
)

for /f "delims=" %%i in ('where python 2^>nul') do (
  set "PYTHON=%%i"
  goto have_python
)

echo Python interpreter not found. Set DSH_PYTHON or put python on PATH.
exit /b 1

:have_python
set "PYTHONPATH=%~dp0deps"
if not defined PORT set "PORT=8765"

echo Billing GraphQL -^> http://127.0.0.1:%PORT%/
"%PYTHON%" "%~dp0server.py"
