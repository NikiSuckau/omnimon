# PowerShell script to build Android APK with Buildozer (cleaned)
param(
    [switch]$Clean = $false,
    [switch]$Release = $false
)

$ErrorActionPreference = "Stop"

Write-Host "=== Omnipet Android Build ===" -ForegroundColor Cyan

# Configuration
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$WSLBuildDir = "~/omnipet_build"
$BuildType = if ($Release) { "release" } else { "debug" }

Write-Host "[1/4] Preparing build directory..." -ForegroundColor Yellow
wsl bash -c "mkdir -p $WSLBuildDir/{core,components,scenes,assets,modules,config,save}"

Write-Host "[2/4] Syncing files to WSL..." -ForegroundColor Yellow
wsl bash -c "rsync -avu --delete --exclude='__pycache__' --exclude='*.pyc' /mnt/e/Omnipet/core/ $WSLBuildDir/core/"
wsl bash -c "rsync -avu --delete --exclude='__pycache__' --exclude='*.pyc' /mnt/e/Omnipet/components/ $WSLBuildDir/components/"
wsl bash -c "rsync -avu --delete --exclude='__pycache__' --exclude='*.pyc' /mnt/e/Omnipet/scenes/ $WSLBuildDir/scenes/"
wsl bash -c "cp /mnt/e/Omnipet/vpet.py $WSLBuildDir/vpet.py"
wsl bash -c "rsync -avu --delete /mnt/e/Omnipet/assets/ $WSLBuildDir/assets/"
wsl bash -c "rsync -avu --delete /mnt/e/Omnipet/modules/ $WSLBuildDir/modules/"
wsl bash -c "rsync -avu --delete /mnt/e/Omnipet/config/ $WSLBuildDir/config/"
wsl bash -c "rsync -avu --delete /mnt/e/Omnipet/save/ $WSLBuildDir/save/"
wsl bash -c "cp /mnt/e/Omnipet/main_android.py $WSLBuildDir/main.py"
wsl bash -c "cp /mnt/e/Omnipet/buildozer.spec $WSLBuildDir/"

# Clean caches
Write-Host "[3/4] Cleaning Python bytecode cache..." -ForegroundColor Yellow
wsl bash -c "cd $WSLBuildDir && find . -type f -name '*.pyc' -delete && find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true"
if ($Clean) { wsl bash -c "cd $WSLBuildDir && rm -rf .buildozer bin" }

Write-Host "[4/4] Building APK ($BuildType)..." -ForegroundColor Yellow
$buildCommand = if ($Release) { "cd $WSLBuildDir && buildozer android clean && buildozer android release" } else { "cd $WSLBuildDir && buildozer android clean && buildozer android debug" }
wsl bash -c $buildCommand

if ($LASTEXITCODE -eq 0) {
    Write-Host "=== Build Successful ===" -ForegroundColor Green
    New-Item -ItemType Directory -Force -Path "$ProjectRoot\bin" | Out-Null
    wsl bash -c "cp $WSLBuildDir/bin/*.apk /mnt/e/Omnipet/bin/"
    Get-ChildItem "$ProjectRoot\bin\*.apk" | ForEach-Object { Write-Host "  $($_.Name)" -ForegroundColor Cyan }
} else {
    Write-Host "=== Build Failed ===" -ForegroundColor Red
}