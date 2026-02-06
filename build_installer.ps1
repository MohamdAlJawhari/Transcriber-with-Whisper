param(
    [ValidateSet('cpu','gpu')]
    [string]$Flavor = 'cpu'
)

$ErrorActionPreference = 'Stop'
$projectRoot = (Get-Location).Path

if ($Flavor -eq 'gpu') {
    $sourceDir = 'dist\FlaskTranscriber'
} else {
    $sourceDir = 'dist_cpu\FlaskTranscriber'
}

if (-not (Test-Path (Join-Path $projectRoot $sourceDir))) {
    Write-Error "Build not found: $sourceDir. Run the build script first."
    exit 1
}

$isccCandidates = @(
    "$Env:ProgramFiles(x86)\Inno Setup 6\ISCC.exe",
    "$Env:ProgramFiles\Inno Setup 6\ISCC.exe"
)

$iscc = $isccCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $iscc) {
    Write-Error 'Inno Setup not found. Install Inno Setup 6, then re-run this script.'
    exit 1
}

& $iscc "/DAppSourceDir=$sourceDir" "/DOutputDir=dist_installer" "installer.iss"
