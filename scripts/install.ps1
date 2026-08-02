[CmdletBinding()]
param([switch]$NoBuild)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

function Invoke-QarCompose {
    param([Parameter(Mandatory = $true)][string[]]$ComposeArgs)
    if ($script:UseDockerPlugin) { & docker compose @ComposeArgs }
    else { & docker-compose @ComposeArgs }
    if ($LASTEXITCODE -ne 0) { throw "Docker Compose falhou: $($ComposeArgs -join ' ')" }
}

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw "Docker não encontrado. Instale e inicie o Docker Desktop."
}
$script:UseDockerPlugin = $false
try {
    & docker compose version *> $null
    $script:UseDockerPlugin = $LASTEXITCODE -eq 0
} catch {
    $script:UseDockerPlugin = $false
}
if (-not $script:UseDockerPlugin -and -not (Get-Command docker-compose -ErrorAction SilentlyContinue)) {
    throw "Docker Compose v2 não encontrado."
}
& docker info *> $null
if ($LASTEXITCODE -ne 0) { throw "O daemon do Docker não está acessível. Inicie o Docker Desktop." }

if (-not (Test-Path -LiteralPath ".env")) {
    Copy-Item -LiteralPath ".env.example" -Destination ".env"
    Write-Host "[config] .env criado com acesso restrito ao computador local."
}

Invoke-QarCompose -ComposeArgs @("config", "--quiet")
$up = @("up", "-d")
if (-not $NoBuild) { $up += "--build" }
Invoke-QarCompose -ComposeArgs $up

$pronto = $false
for ($tentativa = 1; $tentativa -le 60; $tentativa++) {
    try {
        $codigo = "fetch('http://127.0.0.1:3001/api/health').then(r=>r.json()).then(j=>{if(!j.ok||!j.mqtt_connected||j.devices<1)process.exit(2);console.log(JSON.stringify(j))}).catch(()=>process.exit(3))"
        if ($script:UseDockerPlugin) { & docker compose exec -T backend node -e $codigo *> $null }
        else { & docker-compose exec -T backend node -e $codigo *> $null }
        if ($LASTEXITCODE -eq 0) { $pronto = $true; break }
    } catch { }
    Start-Sleep -Seconds 2
}

if (-not $pronto) {
    Write-Host "[erro] O stack não ficou pronto no prazo." -ForegroundColor Red
    try { Invoke-QarCompose -ComposeArgs @("ps") } catch { }
    try { Invoke-QarCompose -ComposeArgs @("logs", "--tail", "80", "backend", "demo") } catch { }
    exit 1
}

$porta = 3001
$linha = Get-Content -LiteralPath ".env" | Where-Object { $_ -match '^DASHBOARD_PORT=' } | Select-Object -First 1
if ($linha) { $porta = [int](($linha -split '=', 2)[1]) }
Write-Host ""
Write-Host "Instalação concluída." -ForegroundColor Green
Write-Host "Dashboard: http://localhost:$porta"
$comandoCompose = if ($script:UseDockerPlugin) { "docker compose" } else { "docker-compose" }
Write-Host "Parar:     $comandoCompose down"
Write-Host "Logs:      $comandoCompose logs -f backend demo"
