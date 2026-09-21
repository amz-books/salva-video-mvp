$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot

$codexPython = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$candidates = @(
    'python',
    'py',
    $codexPython
)
$pythonExe = $null
foreach ($candidate in $candidates) {
    try {
        & $candidate --version *> $null
        if ($LASTEXITCODE -eq 0) { $pythonExe = $candidate; break }
    } catch { }
}
if (-not $pythonExe) { throw 'Python 3 não encontrado. Instale Python e execute este arquivo novamente.' }

if ((-not (Test-Path -LiteralPath '.deps\yt_dlp')) -or (-not (Test-Path -LiteralPath '.deps\imageio_ffmpeg'))) {
    & $pythonExe -m pip install --target .deps -r requirements.txt
    if ($LASTEXITCODE -ne 0) { throw 'Não foi possível instalar yt-dlp.' }
}

Write-Host 'Abra http://localhost:8000 no navegador. Pressione Ctrl+C para parar.'
& $pythonExe app.py
