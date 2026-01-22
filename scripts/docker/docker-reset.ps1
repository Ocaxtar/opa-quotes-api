# scripts/docker/docker-reset.ps1
# Full reset of OPA test environment
#
# Usage: .\scripts\docker\docker-reset.ps1 [-Force] [-KeepImages]
#
# Options:
#   -Force         Skip confirmation prompt
#   -KeepImages    Don't remove Docker images (only containers/volumes)
#
# ⚠️  WARNING: This will:
#   - Stop and remove ALL OPA containers
#   - Remove ALL OPA volumes (data loss!)
#   - Remove OPA networks
#   - Optionally remove OPA images

[CmdletBinding()]
param(
    [switch]$Force,
    [switch]$KeepImages
)

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

function Confirm-Action {
    param([string]$Prompt)
    
    if ($Force) { return $true }
    
    $response = Read-Host "$Prompt (y/N)"
    return $response -eq 'y' -or $response -eq 'Y'
}

function Stop-ComposeServices {
    Write-Host "=== Stopping docker-compose services ===" -ForegroundColor Cyan
    
    $composeFiles = Get-ChildItem -Path $PSScriptRoot\..\..\.. -Recurse -Include docker-compose*.yml,docker-compose*.yaml -ErrorAction SilentlyContinue
    
    if ($composeFiles) {
        foreach ($file in $composeFiles) {
            $dir = $file.DirectoryName
            Write-Host "  Stopping services in $($file.Name)"
            Push-Location $dir
            docker-compose -f $file.Name down --remove-orphans 2>$null
            Pop-Location
        }
        Write-Host "✓ Docker Compose services stopped" -ForegroundColor Green
    } else {
        Write-Host "No docker-compose files found" -ForegroundColor Cyan
    }
}

function Remove-AllContainers {
    Write-Host "`n=== Removing OPA containers ===" -ForegroundColor Cyan
    
    $containers = docker ps -aq --filter "name=opa-"
    
    if (-not $containers) {
        Write-Host "No containers to remove" -ForegroundColor Cyan
        return
    }
    
    $count = ($containers | Measure-Object).Count
    Write-Host "  Found $count container(s)"
    
    $containers | ForEach-Object { docker rm -f $_ 2>$null }
    Write-Host "✓ Containers removed" -ForegroundColor Green
}

function Remove-AllVolumes {
    Write-Host "`n=== Removing OPA volumes ===" -ForegroundColor Cyan
    
    $volumes = docker volume ls -q | Where-Object { $_ -match 'opa' }
    
    if (-not $volumes) {
        Write-Host "No volumes to remove" -ForegroundColor Cyan
        return
    }
    
    $count = ($volumes | Measure-Object).Count
    Write-Host "  Found $count volume(s)"
    $volumes | ForEach-Object { Write-Host "    $_" }
    
    $volumes | ForEach-Object { docker volume rm -f $_ 2>$null }
    Write-Host "✓ Volumes removed" -ForegroundColor Green
}

function Remove-AllNetworks {
    Write-Host "`n=== Removing OPA networks ===" -ForegroundColor Cyan
    
    $networks = docker network ls --filter "name=opa-" --format "{{.Name}}" | Where-Object { $_ -notmatch 'bridge|host|none' }
    
    if (-not $networks) {
        Write-Host "No networks to remove" -ForegroundColor Cyan
        return
    }
    
    $count = ($networks | Measure-Object).Count
    Write-Host "  Found $count network(s)"
    
    $networks | ForEach-Object { docker network rm $_ 2>$null }
    Write-Host "✓ Networks removed" -ForegroundColor Green
}

function Remove-AllImages {
    if ($KeepImages) {
        Write-Host "`n=== Keeping Docker images (-KeepImages flag) ===" -ForegroundColor Cyan
        return
    }
    
    Write-Host "`n=== Removing OPA images ===" -ForegroundColor Cyan
    
    $images = docker images --filter "reference=opa-*" --format "{{.Repository}}:{{.Tag}}"
    
    if (-not $images) {
        Write-Host "No images to remove" -ForegroundColor Cyan
        return
    }
    
    $count = ($images | Measure-Object).Count
    Write-Host "  Found $count image(s)"
    $images | ForEach-Object { Write-Host "    $_" }
    
    $images | ForEach-Object { docker rmi -f $_ 2>$null }
    Write-Host "✓ Images removed" -ForegroundColor Green
}

function Invoke-SystemPrune {
    Write-Host "`n=== Pruning Docker system ===" -ForegroundColor Cyan
    
    # Prune build cache
    docker builder prune -f 2>$null
    
    # Prune dangling images
    docker image prune -f 2>$null
    
    Write-Host "✓ System pruned" -ForegroundColor Green
}

function Show-DiskSpace {
    Write-Host "`n=== Docker Disk Usage ===" -ForegroundColor Cyan
    docker system df
}

# Main execution
Test-DockerRunning

Write-Host "=== OPA Machine Full Reset ===`n" -ForegroundColor Cyan
Write-Host "⚠️  WARNING: This will remove ALL OPA containers, volumes, and networks!" -ForegroundColor Red

if (-not $KeepImages) {
    Write-Host "⚠️  Docker images will also be removed!" -ForegroundColor Red
}

Write-Host ""

# Show what will be affected
Write-Host "Current OPA resources:" -ForegroundColor Yellow
$containerCount = (docker ps -aq --filter "name=opa-" | Measure-Object).Count
$volumeCount = (docker volume ls -q | Where-Object { $_ -match 'opa' } | Measure-Object).Count
Write-Host "  Containers: $containerCount"
Write-Host "  Volumes: $volumeCount"

Write-Host ""

if (-not (Confirm-Action "⚠️  Proceed with full reset?")) {
    Write-Host "Reset cancelled" -ForegroundColor Yellow
    exit 0
}

# Execute reset steps
Stop-ComposeServices
Remove-AllContainers
Remove-AllVolumes
Remove-AllNetworks
Remove-AllImages
Invoke-SystemPrune
Show-DiskSpace

Write-Host "`n✓ Full reset complete" -ForegroundColor Green
Write-Host "`nTo start fresh, run:"
Write-Host "  docker-compose up -d"
