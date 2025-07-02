# WebSocket功能测试脚本
Write-Host "🧪 测试WebSocket和Redis集成..." -ForegroundColor Yellow

# 测试Redis连接
Write-Host "1. 测试Redis连接..." -ForegroundColor Cyan
$env:PATH += ";$env:USERPROFILE\scoop\shims"
try {
    $redisResult = redis-cli ping
    if ($redisResult -eq "PONG") {
        Write-Host "   ✅ Redis连接正常" -ForegroundColor Green
    } else {
        Write-Host "   ❌ Redis连接失败" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "   ❌ Redis连接失败: $_" -ForegroundColor Red
    exit 1
}

# 测试Django后端连接
Write-Host "2. 测试Django后端连接..." -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest -Uri "http://127.0.0.1:8000/admin/" -UseBasicParsing -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Write-Host "   ✅ Django后端连接正常" -ForegroundColor Green
    } else {
        Write-Host "   ❌ Django后端连接失败，状态码: $($response.StatusCode)" -ForegroundColor Red
    }
} catch {
    Write-Host "   ❌ Django后端连接失败: $_" -ForegroundColor Red
}

# 测试前端连接
Write-Host "3. 测试前端连接..." -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5173/" -UseBasicParsing -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Write-Host "   ✅ 前端连接正常" -ForegroundColor Green
    } else {
        Write-Host "   ❌ 前端连接失败，状态码: $($response.StatusCode)" -ForegroundColor Red
    }
} catch {
    Write-Host "   ❌ 前端连接失败: $_" -ForegroundColor Red
}

Write-Host "`n🎉 集成测试完成！" -ForegroundColor Green
Write-Host "🌐 应用访问地址:" -ForegroundColor Yellow
Write-Host "   前端: http://localhost:5173" -ForegroundColor Cyan
Write-Host "   后端: http://127.0.0.1:8000" -ForegroundColor Cyan
Write-Host "   管理后台: http://127.0.0.1:8000/admin" -ForegroundColor Cyan
Write-Host "   Redis: redis://localhost:6379" -ForegroundColor Cyan
