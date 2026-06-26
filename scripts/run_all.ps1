Write-Host "====================================="
Write-Host " UAV Python + C++ Full Pipeline"
Write-Host "====================================="

# Move to repo root
Set-Location $PSScriptRoot\..

$RootDir = Get-Location
$PythonDir = Join-Path $RootDir "env_generator"
$CppDir = Join-Path $RootDir "cpp_engine"
$DataDir = Join-Path $RootDir "data"
$PlotsDir = Join-Path $RootDir "plots"
$OutputsDir = Join-Path $RootDir "outputs"

Write-Host ""
Write-Host "[INFO] Root directory: $RootDir"

# -------------------------------
# Step 1: Clean generated files
# -------------------------------

Write-Host ""
Write-Host "[1] Cleaning old generated files"

New-Item -ItemType Directory -Force -Path $DataDir | Out-Null
New-Item -ItemType Directory -Force -Path $PlotsDir | Out-Null
New-Item -ItemType Directory -Force -Path $OutputsDir | Out-Null

# Clean data folder but keep .gitkeep
Get-ChildItem -Path $DataDir -Force |
Where-Object { $_.Name -ne ".gitkeep" } |
Remove-Item -Recurse -Force

# Clean plots folder but keep .gitkeep
Get-ChildItem -Path $PlotsDir -Force |
Where-Object { $_.Name -ne ".gitkeep" } |
Remove-Item -Recurse -Force

# Clean outputs folder but keep .gitkeep
Get-ChildItem -Path $OutputsDir -Force |
Where-Object { $_.Name -ne ".gitkeep" } |
Remove-Item -Recurse -Force

# Recreate .gitkeep if missing
New-Item -ItemType File -Force -Path (Join-Path $DataDir ".gitkeep") | Out-Null
New-Item -ItemType File -Force -Path (Join-Path $PlotsDir ".gitkeep") | Out-Null
New-Item -ItemType File -Force -Path (Join-Path $OutputsDir ".gitkeep") | Out-Null

Write-Host "[OK] Cleaned data/, plots/, and outputs/ while keeping .gitkeep"

# -------------------------------
# Step 2: Run Python generator
# -------------------------------

Write-Host ""
Write-Host "[2] Running Python generator"

Set-Location $PythonDir

$PythonExe = Join-Path $PythonDir "venv\Scripts\python.exe"

if (!(Test-Path $PythonExe)) {
    Write-Host "[ERROR] Python venv not found at:"
    Write-Host $PythonExe
    Write-Host ""
    Write-Host "Create it using:"
    Write-Host "cd env_generator"
    Write-Host "py -3.11 -m venv venv"
    Write-Host ".\venv\Scripts\activate"
    Write-Host "pip install -r requirements.txt"
    exit 1
}

& $PythonExe main.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Python generator failed"
    exit 1
}

Write-Host "[OK] Python generator completed"

# -------------------------------
# Step 3: Validate generated CSVs
# -------------------------------

Write-Host ""
Write-Host "[3] Validating generated CSV files"

Set-Location $RootDir

$RequiredFiles = @(
    "data\terrain_height.csv",
    "data\terrain_type.csv",
    "data\sensor.csv",
    "data\nfz.csv",
    "data\env.csv"
)

foreach ($file in $RequiredFiles) {
    if (!(Test-Path $file)) {
        Write-Host "[ERROR] Missing required file: $file"
        exit 1
    }
    else {
        Write-Host "[OK] Found $file"
    }
}

# -------------------------------
# Step 4: Build C++ engine
# -------------------------------

Write-Host ""
Write-Host "[4] Building C++ engine"

Set-Location $CppDir

cmake -S . -B build

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] CMake configuration failed"
    exit 1
}

cmake --build build --config Release

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] C++ build failed"
    exit 1
}

Write-Host "[OK] C++ build completed"

# -------------------------------
# Step 5: Run C++ executable
# -------------------------------

Write-Host ""
Write-Host "[5] Running C++ engine"

Set-Location $RootDir

$CppExe = Join-Path $RootDir "cpp_engine\build\Release\uav_pipeline.exe"

if (!(Test-Path $CppExe)) {
    Write-Host "[ERROR] C++ executable not found:"
    Write-Host $CppExe
    exit 1
}

& $CppExe

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] C++ pipeline failed"
    exit 1
}

Write-Host "[OK] C++ pipeline completed"

# -------------------------------
# Step 6: Validate C++ output
# -------------------------------

Write-Host ""
Write-Host "[6] Validating C++ output files"

$FinalCostFile = Join-Path $OutputsDir "final_cost.csv"

if (!(Test-Path $FinalCostFile)) {
    Write-Host "[ERROR] Missing output file:"
    Write-Host $FinalCostFile
    exit 1
}
else {
    Write-Host "[OK] Found outputs\final_cost.csv"
}

# -------------------------------
# Done
# -------------------------------

Write-Host ""
Write-Host "====================================="
Write-Host " FULL PIPELINE COMPLETED SUCCESSFULLY"
Write-Host "====================================="

Write-Host ""
Write-Host "CSV input files:"
Write-Host $DataDir

Write-Host ""
Write-Host "Plot files:"
Write-Host $PlotsDir

Write-Host ""
Write-Host "C++ output files:"
Write-Host $OutputsDir