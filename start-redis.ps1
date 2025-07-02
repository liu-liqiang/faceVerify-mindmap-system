# Redis服务器启动脚本
Write-Host "🔴 启动 Redis 服务器..." -ForegroundColor Yellow

# 添加Scoop路径到环境变量
$env:PATH += ";$env:USERPROFILE\scoop\shims"

# 检查Redis是否已经在运行
try {
    $result = redis-cli ping 2>$null
    if ($result -eq "PONG") {
        Write-Host "✅ Redis 已经在运行中" -ForegroundColor Green
        exit 0
    }
} catch {
    # Redis未运行，继续启动
}

# 启动Redis服务器
Write-Host "启动 Redis 服务器，使用配置文件: redis.conf" -ForegroundColor Gray
redis-server redis.conf
