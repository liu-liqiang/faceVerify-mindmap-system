# 停止开发服务器
Write-Host "🛑 停止开发服务器..." -ForegroundColor Red

Get-Job | Stop-Job
Get-Job | Remove-Job

Write-Host "✅ 所有服务已停止" -ForegroundColor Green
