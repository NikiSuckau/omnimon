# PowerShell GamePi build script for Omnipet Virtual Pet Game
# Creates a GamePi (Raspberry Pi) version

param(
    [string]$Version = "0.9.8"
)

$RELEASE_DIR = "..\Release"
$BUILD_NAME = "Omnipet_GamePi_Ver_$Version"
$TEMP_DIR = "..\temp_gamepi_build"

function Write-Status {
    param([string]$Message)
    Write-Host "[GAMEPI] $Message" -ForegroundColor Yellow
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

if (-not (Test-Path "..\utilities\setup.sh")) {
    Write-Error-Message "utilities\setup.sh not found"
    exit 1
}

Write-Status "Building GamePi (Raspberry Pi) version..."

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
Copy-Item "..\config\config_raspberry.json" "$TEMP_DIR\$BUILD_NAME\config\config.json"
Copy-Item "..\config\input_config_raspberry.json" "$TEMP_DIR\$BUILD_NAME\config\input_config.json"

# Copy documentation
Write-Status "Copying documentation..."
Copy-Item -Recurse "..\Documentation" "$TEMP_DIR\$BUILD_NAME\"

# Copy core directory (excluding __pycache__ folders)
Write-Status "Copying core directory..."
$coreSource = (Resolve-Path "..\core").Path
$coreDestination = "$TEMP_DIR\$BUILD_NAME\core"
robocopy $coreSource $coreDestination /E /XD "__pycache__" /NFL /NDL /NJH /NJS /nc /ns /np | Out-Null

# Copy components directory
Write-Status "Copying components directory..."
$compSource = (Resolve-Path "..\components").Path
$compDestination = "$TEMP_DIR\$BUILD_NAME\components"
robocopy $compSource $compDestination /E /XD "__pycache__" /NFL /NDL /NJH /NJS /nc /ns /np | Out-Null

# Copy scenes directory
Write-Status "Copying scenes directory..."
$scenesSource = (Resolve-Path "..\scenes").Path
$scenesDestination = "$TEMP_DIR\$BUILD_NAME\scenes"
robocopy $scenesSource $scenesDestination /E /XD "__pycache__" /NFL /NDL /NJH /NJS /nc /ns /np | Out-Null

# Copy vpet.py
Write-Status "Copying vpet.py..."
Copy-Item "..\vpet.py" "$TEMP_DIR\$BUILD_NAME\"

# Copy modules
Write-Status "Copying modules..."
Copy-Item -Recurse "..\modules" "$TEMP_DIR\$BUILD_NAME\"

# Copy network
Write-Status "Copying network..."
Copy-Item -Recurse "..\network" "$TEMP_DIR\$BUILD_NAME\"

# Create empty save folder
Write-Status "Creating save directory..."
New-Item -ItemType Directory -Path "$TEMP_DIR\$BUILD_NAME\save" -Force | Out-Null

# Copy Python files and scripts
Write-Status "Copying Python files and launch scripts..."
Copy-Item "..\__init__.py" "$TEMP_DIR\$BUILD_NAME\"
Copy-Item "..\launch.sh" "$TEMP_DIR\$BUILD_NAME\"
Copy-Item "..\LICENSE.txt" "$TEMP_DIR\$BUILD_NAME\"
Copy-Item "..\main.py" "$TEMP_DIR\$BUILD_NAME\"

# Copy setup script from utilities
Write-Status "Copying setup script..."
Copy-Item "..\utilities\setup.sh" "$TEMP_DIR\$BUILD_NAME\"

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
    Write-Success "GamePi build completed: $BUILD_NAME"
    Get-ChildItem "$RELEASE_DIR\$BUILD_NAME.zip" | Format-Table Name, Length, LastWriteTime
} else {
    Write-Error-Message "Failed to create release archive"
    exit 1
}
