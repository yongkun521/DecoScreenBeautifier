param(
    [string]$Python = "",
    [switch]$Clean
)

$root = Split-Path -Parent $PSScriptRoot
$spec = Join-Path $root "DecoScreenBeautifier.spec"

if (-not (Test-Path $spec)) {
    Write-Error "Spec file not found: $spec"
    exit 1
}

if (-not $Python) {
    $venvPython = Join-Path $root "venv\\Scripts\\python.exe"
    if (Test-Path $venvPython) {
        $Python = $venvPython
    } else {
        $Python = "python"
    }
}

if ($Clean) {
    $buildDir = Join-Path $root "build"
    $distDir = Join-Path $root "dist"
    if (Test-Path $buildDir) {
        Remove-Item -Recurse -Force $buildDir
    }
    if (Test-Path $distDir) {
        Remove-Item -Recurse -Force $distDir
    }
}

& $Python -m PyInstaller $spec
