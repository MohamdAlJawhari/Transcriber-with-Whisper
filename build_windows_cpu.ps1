$ErrorActionPreference = 'Stop'

$projectRoot = (Get-Location).Path
$venvPath = Join-Path $projectRoot '.venv-cpu'
$pythonExe = Join-Path $venvPath 'Scripts\python.exe'
$pipExe = Join-Path $venvPath 'Scripts\pip.exe'
$pyinstallerExe = Join-Path $venvPath 'Scripts\pyinstaller.exe'

if (-not (Test-Path $pythonExe)) {
    python -m venv $venvPath
}

& $pythonExe -m pip install --upgrade pip

# CPU-only PyTorch
& $pipExe install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# App deps + packager
& $pipExe install librosa transformers soundfile werkzeug flask "numpy<2" waitress
& $pipExe install pyinstaller

& $pyinstallerExe `
    --noconsole `
    --onedir `
    --name "FlaskTranscriber" `
    --icon "app.ico" `
    --add-data "templates;templates" `
    --add-data "static;static" `
    --add-data "model;model" `
    --distpath "dist_cpu" `
    --workpath "build_cpu" `
    launcher.py
