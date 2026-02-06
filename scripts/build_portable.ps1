param(
    [string]$DistDir = "dist\\DecoScreenBeautifier",
    [string]$Output = ""
)

$root = Split-Path -Parent $PSScriptRoot
$distPath = Join-Path $root $DistDir

if (-not (Test-Path $distPath)) {
    Write-Error "Dist folder not found: $distPath"
    exit 1
}

if (-not $Output) {
    $Output = Join-Path $root "dist\\DecoScreenBeautifier_portable.zip"
}

if (Test-Path $Output) {
    Remove-Item -Force $Output
}

Compress-Archive -Path (Join-Path $distPath "*") -DestinationPath $Output
