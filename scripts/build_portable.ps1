param(
    [string]$DistDir = "dist\\DecoScreenBeautifier",
    [string]$Output = "",
    [switch]$IncludeBundledWT,
    [string]$BundledWTSource = "",
    [string]$BundledWTTarget = "vendor\\windows_terminal\\x64"
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

    $targetDir = Resolve-FullPath -PathText (Join-Path $DistDir $BundledWTTarget)
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
    $wtMetaTarget = Resolve-FullPath -PathText (Join-Path $DistDir "vendor\\windows_terminal")
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

if (Test-Path $Output) {
    Remove-Item -Force $Output
}

Compress-Archive -Path (Join-Path $distPath "*") -DestinationPath $Output
