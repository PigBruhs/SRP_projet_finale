# 水稻病害检测API启动脚本 (PowerShell)
Write-Host "启动水稻病害检测API服务..." -ForegroundColor Green
Write-Host ""

# 检查Python是否安装
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ 找到Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ 错误: 未找到Python，请先安装Python 3.8+" -ForegroundColor Red
    Read-Host "按回车键退出"
    exit 1
}

# 检查依赖是否安装
Write-Host "检查依赖包..." -ForegroundColor Yellow
try {
    $flaskInstalled = pip show flask 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Flask已安装" -ForegroundColor Green
    } else {
        throw "Flask未安装"
    }
} catch {
    Write-Host "安装依赖包..." -ForegroundColor Yellow
    pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ 错误: 依赖安装失败" -ForegroundColor Red
        Read-Host "按回车键退出"
        exit 1
    }
}

# 启动服务
Write-Host "启动API服务..." -ForegroundColor Green
python start.py

Read-Host "按回车键退出"
