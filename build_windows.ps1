$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

$venvPath = Join-Path $projectRoot '.venv'
$pythonExe = Join-Path $venvPath 'Scripts\python.exe'
$pipExe = Join-Path $venvPath 'Scripts\pip.exe'
$pyinstallerExe = Join-Path $venvPath 'Scripts\pyinstaller.exe'

if (-not (Test-Path $pythonExe)) {
    python -m venv $venvPath
}

& $pythonExe -m pip install --upgrade pip
& $pipExe install -r requirements.txt
& $pipExe install pyinstaller

& $pyinstallerExe `
    --noconsole `
    --onedir `
    --name "FlaskTranscriber" `
    --icon "app.ico" `
    --add-data "templates;templates" `
    --add-data "static;static" `
    --add-data "model;model" `
    launcher.py
