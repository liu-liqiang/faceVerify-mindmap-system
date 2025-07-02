# 协作思维导图系统 - 开发环境启动脚本

Write-Host "🚀 启动协作思维导图系统开发环境..." -ForegroundColor Green

# 启动Redis服务器
Write-Host "🔴 启动 Redis 服务器..." -ForegroundColor Yellow
Start-Job -Name "Redis" -ScriptBlock {
    Set-Location "d:\pythonprojects\caseManage\smmproj"
    $env:PATH += ";$env:USERPROFILE\scoop\shims"
    redis-server redis.conf
}

# 等待Redis启动
Start-Sleep -Seconds 2

# 启动后端服务器
Write-Host "📡 启动 Django 后端服务器..." -ForegroundColor Yellow
Start-Job -Name "Backend" -ScriptBlock {
    Set-Location "d:\pythonprojects\caseManage\smmproj\backend"
    $env:DJANGO_SETTINGS_MODULE = "collaboration_system.settings"
    & "D:/pythonprojects/caseManage/smmproj/.venv/Scripts/python.exe" manage.py runserver 127.0.0.1:8000
}

# 等待后端启动
Start-Sleep -Seconds 3

# 启动前端开发服务器
Write-Host "🎨 启动 Vue.js 前端服务器..." -ForegroundColor Yellow
Start-Job -Name "Frontend" -ScriptBlock {
    Set-Location "d:\pythonprojects\caseManage\smmproj\frontend"
    npm run dev
}

Write-Host "`n✅ 服务已启动！" -ForegroundColor Green
Write-Host "🔴 Redis地址: redis://localhost:6379" -ForegroundColor Cyan
Write-Host "🌐 前端地址: http://localhost:5173" -ForegroundColor Cyan
Write-Host "🔧 后端地址: http://localhost:8000" -ForegroundColor Cyan
Write-Host "⚙️  管理面板: http://localhost:8000/admin" -ForegroundColor Cyan
Write-Host "👤 管理员账号: admin / admin123" -ForegroundColor Magenta

Write-Host "`n📋 查看服务状态:" -ForegroundColor Yellow
Write-Host "Get-Job | Format-Table" -ForegroundColor Gray

Write-Host "`n🛑 停止服务:" -ForegroundColor Yellow
Write-Host "Get-Job | Stop-Job; Get-Job | Remove-Job" -ForegroundColor Gray
