# PowerShell Android APK build script for Omnimon Virtual Pet Game

param(
    [string]$Version = "0.9.8"
)

function Write-Status {
    param([string]$Message)
    Write-Host "[ANDROID-APK] $Message" -ForegroundColor Yellow
}

function Write-Error-Message {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor Green
}

Write-Status "Starting Android APK build..."

# Clean global buildozer directory
$globalBuildozerDir = Join-Path $env:USERPROFILE ".buildozer"
if (Test-Path $globalBuildozerDir) {
    Write-Status "Cleaning global .buildozer directory..."
    Remove-Item -Recurse -Force $globalBuildozerDir
}

# Get the root directory of the project
$rootDir = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$specPath = Join-Path $rootDir "buildozer.spec"

# Clean local buildozer directory
$buildozerDir = Join-Path $rootDir ".buildozer"
if (Test-Path $buildozerDir) {
    Write-Status "Cleaning local .buildozer directory..."
    Remove-Item -Recurse -Force $buildozerDir
}

# Check for buildozer.spec
if (-not (Test-Path $specPath)) {
    Write-Error-Message "buildozer.spec not found at '$specPath'. Please ensure the file exists in the root project directory."
    exit 1
}

# Update version in buildozer.spec
Write-Status "Updating version to $Version in buildozer.spec..."
(Get-Content $specPath) -replace 'version = .*', "version = $Version" | Set-Content $specPath

# Run Buildozer within WSL
Write-Status "Running Buildozer to build the APK via WSL..."
Write-Status "This may take a long time on the first run as it downloads the Android SDK/NDK..."
$tempScriptPath = Join-Path $PSScriptRoot "temp_wsl_build.sh"
try {
    # Convert the project path to a WSL-compatible path
    $wslPath = wsl wslpath -a $rootDir
    if ($LASTEXITCODE -ne 0 -or -not $wslPath) {
        throw "Failed to convert path '$rootDir' to WSL path."
    }

    # Create a temporary shell script to run in WSL
    # Note: We escape PowerShell variables `$` with a backtick `
    $scriptContent = @"
#!/bin/bash
export PATH="`$HOME/.local/bin:`$PATH"
cd "$wslPath"
echo "--- Running in WSL ---"
echo "Current directory: `$(pwd)"
echo "PATH: `$PATH"
echo "Checking for buildozer..."
which buildozer
if [ `$? -ne 0 ]; then
    echo "Buildozer not found in PATH."
    exit 1
fi
echo "----------------------"
buildozer -v android debug
"@
    # Use -NoNewline to avoid issues with script execution
    Set-Content -Path $tempScriptPath -Value $scriptContent -Encoding Ascii -NoNewline

    # Convert temp script path to WSL path
    $wslScriptPath = wsl wslpath -a $tempScriptPath
    if ($LASTEXITCODE -ne 0 -or -not $wslScriptPath) {
        throw "Failed to convert path '$tempScriptPath' to WSL path."
    }

    # Make the script executable inside WSL
    wsl chmod +x $wslScriptPath
    
    # Execute the command
    wsl $wslScriptPath
    
    $exitCode = $LASTEXITCODE

    if ($exitCode -ne 0) {
        throw "Buildozer (via WSL) failed with exit code $exitCode"
    }
} catch {
    Write-Error-Message "Buildozer process failed: $_"
    Write-Error-Message "Please ensure WSL is installed and configured with all dependencies (see ANDROID_README.txt)."
    exit 1
} finally {
    # Clean up the temporary script
    if (Test-Path $tempScriptPath) {
        Remove-Item $tempScriptPath -Force
    }
}

# Copy APK to Release folder
$apkName = "Omnimon-$Version-debug.apk"
$apkPath = Join-Path $rootDir "bin" $apkName

if (Test-Path $apkPath) {
    $releaseDir = Join-Path $rootDir "Release"
    if (-not (Test-Path $releaseDir)) {
        New-Item -ItemType Directory -Path $releaseDir | Out-Null
    }
    $finalApkName = "Omnimon_Android_Ver_$Version.apk"
    Copy-Item $apkPath (Join-Path $releaseDir $finalApkName) -Force
    Write-Success "APK successfully built and copied to Release folder: $finalApkName"
} else {
    Write-Error-Message "Build failed. APK not found at '$apkPath'"
    exit 1
}

Write-Success "Android APK build process completed."
