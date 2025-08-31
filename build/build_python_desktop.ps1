# PowerShell Python Desktop build script for Omnimon Virtual Pet Game
# Creates a Python desktop version for Windows and Linux

param(
    [string]$Version = "0.9.8"
)

$RELEASE_DIR = "..\Release"
$BUILD_NAME = "Omnimon_Python_Desktop_Ver_$Version"
$TEMP_DIR = "..\temp_python_desktop_build"

function Write-Status {
    param([string]$Message)
    Write-Host "[PYTHON] $Message" -ForegroundColor Yellow
}

function Write-Error-Message {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor Green
}

# Check if required files exist
if (-not (Test-Path "..\main.py")) {
    Write-Error-Message "main.py not found"
    exit 1
}

Write-Status "Building Python Desktop version..."

# Clean previous builds
Write-Status "Cleaning previous builds..."
if (Test-Path $TEMP_DIR) { Remove-Item -Recurse -Force $TEMP_DIR }

# Create temporary build directory
New-Item -ItemType Directory -Path "$TEMP_DIR\$BUILD_NAME" -Force | Out-Null

# Copy assets
Write-Status "Copying assets..."
Copy-Item -Recurse "..\assets" "$TEMP_DIR\$BUILD_NAME\"

# Copy and rename config files
Write-Status "Copying configuration files..."
New-Item -ItemType Directory -Path "$TEMP_DIR\$BUILD_NAME\config" -Force | Out-Null
Copy-Item "..\config\config_python_desktop.json" "$TEMP_DIR\$BUILD_NAME\config\config.json"
Copy-Item "..\config\input_config_python_desktop.json" "$TEMP_DIR\$BUILD_NAME\config\input_config.json"

# Copy documentation
Write-Status "Copying documentation..."
Copy-Item -Recurse "..\Documentation" "$TEMP_DIR\$BUILD_NAME\"

# Copy game directory (excluding __pycache__ folders)
Write-Status "Copying game directory..."
$gameSource = (Resolve-Path "..\game").Path
$gameDestination = "$TEMP_DIR\$BUILD_NAME\game"
robocopy $gameSource $gameDestination /E /XD "__pycache__" /NFL /NDL /NJH /NJS /nc /ns /np | Out-Null
if ($LASTEXITCODE -ge 8) {
    Write-Error-Message "Failed to copy game directory using robocopy. Check if robocopy is in your system's PATH."
    exit 1
}

# Copy Module Editor (excluding Source folder)
Write-Status "Copying Module Editor..."
New-Item -ItemType Directory -Path "$TEMP_DIR\$BUILD_NAME\Module Editor" -Force | Out-Null
Get-ChildItem "..\Module Editor" | Where-Object { $_.Name -ne "Source" } | ForEach-Object {
    Copy-Item -Recurse $_.FullName "$TEMP_DIR\$BUILD_NAME\Module Editor\"
}

# Copy modules
Write-Status "Copying modules..."
Copy-Item -Recurse "..\modules" "$TEMP_DIR\$BUILD_NAME\"

# Create empty save folder
Write-Status "Creating save directory..."
New-Item -ItemType Directory -Path "$TEMP_DIR\$BUILD_NAME\save" -Force | Out-Null

# Copy Python files and scripts
Write-Status "Copying Python files and launch scripts..."
Copy-Item "..\__init__.py" "$TEMP_DIR\$BUILD_NAME\"
Copy-Item "..\launch.bat" "$TEMP_DIR\$BUILD_NAME\"
Copy-Item "..\launch.sh" "$TEMP_DIR\$BUILD_NAME\"
Copy-Item "..\LICENSE.txt" "$TEMP_DIR\$BUILD_NAME\"
Copy-Item "..\main.py" "$TEMP_DIR\$BUILD_NAME\"
Copy-Item "..\ModuleEditor.bat" "$TEMP_DIR\$BUILD_NAME\"

# Create the ZIP file
Write-Status "Creating ZIP archive..."
if (-not (Test-Path $RELEASE_DIR)) {
    New-Item -ItemType Directory -Path $RELEASE_DIR | Out-Null
}

# Remove existing ZIP file if it exists
$zipPath = "$RELEASE_DIR\$BUILD_NAME.zip"
if (Test-Path $zipPath) {
    Remove-Item $zipPath -Force
}

try {
    Add-Type -AssemblyName "System.IO.Compression.FileSystem"
    $sourcePath = (Resolve-Path "$TEMP_DIR\$BUILD_NAME").Path
    $zipPath = (Resolve-Path $RELEASE_DIR).Path + "\$BUILD_NAME.zip"
    [System.IO.Compression.ZipFile]::CreateFromDirectory($sourcePath, $zipPath)
} catch {
    Write-Error-Message "Failed to create ZIP file: $_"
    exit 1
}

# Clean up
Write-Status "Cleaning up temporary files..."
if (Test-Path $TEMP_DIR) { Remove-Item -Recurse -Force $TEMP_DIR }

if (Test-Path "$RELEASE_DIR\$BUILD_NAME.zip") {
    Write-Success "Python Desktop build completed: $BUILD_NAME"
    Get-ChildItem "$RELEASE_DIR\$BUILD_NAME.zip" | Format-Table Name, Length, LastWriteTime
} else {
    Write-Error-Message "Failed to create release archive"
    exit 1
}
