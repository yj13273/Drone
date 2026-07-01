#!/bin/sh
set -eu

echo "====================================="
echo " UAV Python + C++ Full Pipeline"
echo "====================================="

ROOT_DIR="/app"
PYTHON_DIR="$ROOT_DIR/env_generator"
CPP_DIR="$ROOT_DIR/cpp_engine"
DATA_DIR="$ROOT_DIR/data"
PLOTS_DIR="$ROOT_DIR/plots"
OUTPUTS_DIR="$ROOT_DIR/outputs"
CPP_EXE="$CPP_DIR/build/${CPP_EXECUTABLE_NAME:-uav_pipeline}"

export MPLBACKEND=Agg

echo ""
echo "[INFO] Root directory: $ROOT_DIR"

echo ""
echo "[1] Cleaning old generated files"

mkdir -p "$DATA_DIR" "$PLOTS_DIR" "$OUTPUTS_DIR"

find "$DATA_DIR" -mindepth 1 ! -name ".gitkeep" -exec rm -rf {} +
find "$PLOTS_DIR" -mindepth 1 ! -name ".gitkeep" -exec rm -rf {} +
find "$OUTPUTS_DIR" -mindepth 1 ! -name ".gitkeep" -exec rm -rf {} +

touch "$DATA_DIR/.gitkeep"
touch "$PLOTS_DIR/.gitkeep"
touch "$OUTPUTS_DIR/.gitkeep"

echo "[OK] Cleaned data/, plots/, and outputs/ while keeping .gitkeep"

echo ""
echo "[2] Running Python generator"

cd "$PYTHON_DIR"
python main.py

echo "[OK] Python generator completed"

echo ""
echo "[3] Validating generated CSV files"

cd "$ROOT_DIR"

for file in \
    "data/terrain_height.csv" \
    "data/terrain_type.csv" \
    "data/sensor.csv" \
    "data/nfz.csv" \
    "data/env.csv"
do
    if [ ! -f "$file" ]; then
        echo "[ERROR] Missing required file: $file"
        exit 1
    else
        echo "[OK] Found $file"
    fi
done

echo ""
echo "[4] Checking C++ executable"

if [ ! -f "$CPP_EXE" ]; then
    echo "[ERROR] C++ executable not found:"
    echo "$CPP_EXE"
    exit 1
fi

chmod +x "$CPP_EXE"

echo "[OK] Found C++ executable: $CPP_EXE"

echo ""
echo "[5] Running C++ engine"

cd "$ROOT_DIR"
"$CPP_EXE"

echo "[OK] C++ pipeline completed"

echo ""
echo "[6] Validating C++ output files"

if [ -f "$OUTPUTS_DIR/final_cost.csv" ]; then
    FINAL_COST_FILE="$OUTPUTS_DIR/final_cost.csv"
elif [ -f "$OUTPUTS_DIR/finalcost.csv" ]; then
    FINAL_COST_FILE="$OUTPUTS_DIR/finalcost.csv"
else
    echo "[ERROR] Missing output file. Checked:"
    echo "$OUTPUTS_DIR/final_cost.csv"
    echo "$OUTPUTS_DIR/finalcost.csv"
    exit 1
fi

echo "[OK] Found final cost file:"
echo "$FINAL_COST_FILE"

echo ""
echo "[7] Checking final cost plot script"

FINAL_COST_PLOT_SCRIPT="$PYTHON_DIR/visualization/finalcsv.py"

if [ -f "$FINAL_COST_PLOT_SCRIPT" ]; then
    echo "[INFO] Generating final cost plots..."
    python "$FINAL_COST_PLOT_SCRIPT"
    echo "[OK] Final cost plots generated"
else
    echo "[WARN] env_generator/visualization/finalcsv.py not found. Skipping final cost plots."
fi

echo ""
echo "====================================="
echo " FULL PIPELINE COMPLETED SUCCESSFULLY"
echo "====================================="

echo ""
echo "CSV input files:"
echo "$DATA_DIR"

echo ""
echo "Plot files:"
echo "$PLOTS_DIR"

echo ""
echo "C++ output files:"
echo "$OUTPUTS_DIR"