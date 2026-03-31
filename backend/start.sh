#!/bin/bash

echo "=================================================="
echo "  TankBattle - 坦克对战仿真环境"
echo "=================================================="
echo ""

# 检查 Python 版本
python_version=$(python3 --version 2>&1)
echo "[INFO] Python Version: $python_version"

# 安装依赖（如果需要）
if [ ! -d "venv" ] && [ ! -f "/.dockerenv" ]; then
    echo "[INFO] Installing dependencies..."
    pip install -r requirements.txt -q
fi

echo ""
echo "=================================================="
echo "  Startup Success"
echo "  Frontend: http://localhost:8080"
echo "=================================================="
echo ""

# 启动应用
exec python app.py
