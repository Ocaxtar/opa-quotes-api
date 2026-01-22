# scripts/docker/docker-health.ps1
# Inspect health status of OPA test containers
#
# Usage: .\scripts\docker\docker-health.ps1 [container_name]
# If no container specified, shows all OPA containers

$ErrorActionPreference = "Stop"

function Test-DockerRunning {
    try {
        docker info 2>$null | Out-Null
        return $true
    } catch {
        Write-Host "Error: Docker is not running" -ForegroundColor Red
        exit 1
    }
}

function Format-ContainerStatus {
    param([string]$Status)
    
    switch ($Status) {
        "running" { Write-Host "✓ Running" -ForegroundColor Green -NoNewline }
        "exited" { Write-Host "✗ Exited" -ForegroundColor Red -NoNewline }
        "created" { Write-Host "⚠ Created" -ForegroundColor Yellow -NoNewline }
        "paused" { Write-Host "⏸ Paused" -ForegroundColor Yellow -NoNewline }
        "restarting" { Write-Host "↻ Restarting" -ForegroundColor Yellow -NoNewline }
        default { Write-Host "? $Status" -ForegroundColor Cyan -NoNewline }
    }
}

function Get-HealthStatus {
    param([string]$Container)
    
    try {
        $health = docker inspect --format='{{.State.Health.Status}}' $Container 2>$null
        if ([string]::IsNullOrWhiteSpace($health)) { $health = "none" }
    } catch {
        $health = "none"
    }
    
    switch ($health) {
        "healthy" { Write-Host "✓ Healthy" -ForegroundColor Green -NoNewline }
        "unhealthy" { Write-Host "✗ Unhealthy" -ForegroundColor Red -NoNewline }
        "starting" { Write-Host "⚠ Starting" -ForegroundColor Yellow -NoNewline }
        "none" { Write-Host "- No healthcheck" -ForegroundColor Cyan -NoNewline }
        default { Write-Host $health -NoNewline }
    }
}

function Show-ContainerDetails {
    param([string]$Container)
    
    try {
        docker inspect $Container 2>$null | Out-Null
    } catch {
        Write-Host "Container '$Container' not found" -ForegroundColor Red
        return
    }
    
    Write-Host "=== Container: $Container ===" -ForegroundColor Cyan
    
    # Basic info
    $status = docker inspect --format='{{.State.Status}}' $Container
    $image = docker inspect --format='{{.Config.Image}}' $Container
    $created = docker inspect --format='{{.Created}}' $Container
    $uptime = docker inspect --format='{{.State.StartedAt}}' $Container
    
    Write-Host "Image:   $image"
    Write-Host -NoNewline "Status:  "; Format-ContainerStatus $status; Write-Host ""
    Write-Host -NoNewline "Health:  "; Get-HealthStatus $Container; Write-Host ""
    Write-Host "Created: $created"
    Write-Host "Started: $uptime"
    
    # Ports
    try {
        $ports = docker port $Container 2>$null
        if ($ports) {
            Write-Host "`nPorts:" -ForegroundColor Cyan
            $ports | ForEach-Object { Write-Host "  $_" }
        }
    } catch {}
    
    # Network
    $networks = docker inspect --format='{{range $net,$v := .NetworkSettings.Networks}}{{$net}} {{end}}' $Container
    if ($networks) {
        Write-Host "`nNetworks:" -ForegroundColor Cyan
        Write-Host "  $networks"
    }
    
    # Volumes
    $volumes = docker inspect --format='{{range .Mounts}}{{.Type}}: {{.Source}} -> {{.Destination}}{{"\n"}}{{end}}' $Container
    if ($volumes) {
        Write-Host "`nVolumes:" -ForegroundColor Cyan
        $volumes -split "`n" | Where-Object { $_ } | ForEach-Object { Write-Host "  $_" }
    }
    
    # Environment (filtered for sensitive data)
    Write-Host "`nEnvironment (non-sensitive):" -ForegroundColor Cyan
    $env = docker inspect --format='{{range .Config.Env}}{{println .}}{{end}}' $Container
    $env -split "`n" | Where-Object { $_ -and $_ -notmatch 'password|secret|token|key' } | ForEach-Object { Write-Host "  $_" }
    
    # Recent logs
    Write-Host "`nRecent logs (last 10 lines):" -ForegroundColor Cyan
    docker logs --tail 10 $Container 2>&1 | ForEach-Object { Write-Host "  $_" }
    
    Write-Host ""
}

# Main execution
Test-DockerRunning

$targetContainer = $args[0]

if ($targetContainer) {
    # Show details for specific container
    Show-ContainerDetails $targetContainer
} else {
    # List all OPA containers
    Write-Host "=== OPA Machine Containers ===`n" -ForegroundColor Cyan
    
    $containers = docker ps -a --filter "name=opa-" --format "{{.Names}}" | Sort-Object
    
    if (-not $containers) {
        Write-Host "No OPA containers found" -ForegroundColor Yellow
        Write-Host "`nTo see all containers, run: docker ps -a"
        exit 0
    }
    
    # Table header
    Write-Host ("{0,-30} {1,-15} {2,-15} {3,-20}" -f "CONTAINER", "STATUS", "HEALTH", "IMAGE")
    Write-Host ("{0,-30} {1,-15} {2,-15} {3,-20}" -f ("-" * 30), ("-" * 15), ("-" * 15), ("-" * 20))
    
    # List containers
    foreach ($container in $containers) {
        $status = docker inspect --format='{{.State.Status}}' $container
        $health = docker inspect --format='{{.State.Health.Status}}' $container 2>$null
        if ([string]::IsNullOrWhiteSpace($health)) { $health = "none" }
        $image = (docker inspect --format='{{.Config.Image}}' $container) -split ':' | Select-Object -First 1
        
        # Format status text
        $statusText = switch ($status) {
            "running" { "✓ Running" }
            "exited" { "✗ Exited" }
            "created" { "⚠ Created" }
            default { $status }
        }
        
        $healthText = switch ($health) {
            "healthy" { "✓ Healthy" }
            "unhealthy" { "✗ Unhealthy" }
            "starting" { "⚠ Starting" }
            "none" { "- No check" }
            default { $health }
        }
        
        Write-Host ("{0,-30} {1,-15} {2,-15} {3,-20}" -f $container, $statusText, $healthText, $image)
    }
    
    Write-Host "`nFor detailed info on a specific container, run:"
    Write-Host "  .\scripts\docker\docker-health.ps1 <container_name>"
}
