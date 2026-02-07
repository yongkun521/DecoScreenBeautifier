param(
    [string]$Python = "",
    [switch]$Clean,
    [switch]$IncludeBundledWT,
    [string]$BundledWTSource = "",
    [string]$BundledWTTarget = "vendor\\windows_terminal\\x64"
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

function Resolve-FullPath {
    param([string]$PathText)
    if (-not $PathText) {
        return ""
    }
    if ([System.IO.Path]::IsPathRooted($PathText)) {
        return $PathText
    }
    return Join-Path $root $PathText
}

& $Python -m PyInstaller $spec
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

if ($IncludeBundledWT) {
    if (-not $BundledWTSource) {
        $BundledWTSource = Join-Path $root "vendor\\windows_terminal\\x64"
    } else {
        $BundledWTSource = Resolve-FullPath -PathText $BundledWTSource
    }

    if (-not (Test-Path $BundledWTSource)) {
        Write-Error "Bundled WT source not found: $BundledWTSource"
        exit 1
    }

    $distDir = Join-Path $root "dist"
    if (-not (Test-Path $distDir)) {
        Write-Error "Dist folder not found after build: $distDir"
        exit 1
    }

    $targetDir = Resolve-FullPath -PathText (Join-Path "dist" $BundledWTTarget)
    if (Test-Path $targetDir) {
        Remove-Item -Recurse -Force $targetDir
    }
    New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
    Copy-Item -Path (Join-Path $BundledWTSource "*") -Destination $targetDir -Recurse -Force

    $portableMarker = Join-Path $targetDir ".portable"
    if (-not (Test-Path $portableMarker)) {
        New-Item -ItemType File -Path $portableMarker -Force | Out-Null
    }

    $wtMetaSource = Join-Path $root "vendor\\windows_terminal"
    $wtMetaTarget = Join-Path $distDir "vendor\\windows_terminal"
    if (Test-Path (Join-Path $wtMetaSource "wt_version.json")) {
        New-Item -ItemType Directory -Path $wtMetaTarget -Force | Out-Null
        Copy-Item -Path (Join-Path $wtMetaSource "wt_version.json") -Destination (Join-Path $wtMetaTarget "wt_version.json") -Force
    }
    if (Test-Path (Join-Path $wtMetaSource "licenses")) {
        Copy-Item -Path (Join-Path $wtMetaSource "licenses") -Destination $wtMetaTarget -Recurse -Force
    }
    if (Test-Path (Join-Path $wtMetaSource "shaders")) {
        Copy-Item -Path (Join-Path $wtMetaSource "shaders") -Destination $wtMetaTarget -Recurse -Force
    }

    Write-Host "Bundled Windows Terminal assets copied to: $targetDir"
}
