<#
.SYNOPSIS
    Sobe o Controle Financeiro inteiro: Postgres (Docker), backend (uvicorn) e frontend (Next.js).

.DESCRIPTION
    1. Garante que o Docker Desktop está rodando (inicia se necessário e aguarda o engine responder).
    2. Sobe o Postgres local via `docker compose up -d`.
    3. Abre o backend (uvicorn --reload) em uma nova janela do PowerShell.
    4. Abre o frontend (npm run dev) em outra nova janela.

.EXAMPLE
    .\scripts\start-all.ps1
#>

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot

function Test-DockerReady {
    try {
        docker version *> $null
        return $LASTEXITCODE -eq 0
    } catch {
        return $false
    }
}

# 1. Garante que o Docker Desktop está rodando
if (-not (Test-DockerReady)) {
    $dockerExe = "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    if (-not (Get-Process "Docker Desktop" -ErrorAction SilentlyContinue)) {
        if (-not (Test-Path $dockerExe)) {
            Write-Error "Docker Desktop não encontrado em '$dockerExe'. Instale antes de rodar este script."
            exit 1
        }
        Write-Host "Iniciando o Docker Desktop..."
        Start-Process $dockerExe
    }

    Write-Host "Aguardando o Docker engine responder (pode levar até 2 minutos na primeira vez)..."
    $tries = 0
    while (-not (Test-DockerReady) -and $tries -lt 40) {
        Start-Sleep -Seconds 3
        $tries++
    }
    if (-not (Test-DockerReady)) {
        Write-Error "O Docker não respondeu a tempo. Abra o Docker Desktop manualmente e tente de novo."
        exit 1
    }
}
Write-Host "Docker OK."

# 2. Sobe o Postgres
Write-Host "Subindo o Postgres (docker compose up -d)..."
Push-Location $projectRoot
docker compose up -d
Pop-Location

# 3. Backend em nova janela
Write-Host "Abrindo o backend (uvicorn) em nova janela..."
Start-Process powershell -ArgumentList @(
    "-NoExit", "-Command",
    "cd '$projectRoot\api'; & '$projectRoot\.venv\Scripts\python.exe' -m uvicorn index:app --reload --host 127.0.0.1 --port 8000"
)

# Se a pasta .next foi deixada por um build de produção (`next build`), ela é
# incompatível com `next dev` e causa erros "Cannot find module './NNN.js'".
# Limpa nesse caso específico para não herdar um cache misto.
$prerenderManifest = Join-Path $projectRoot ".next\prerender-manifest.json"
if (Test-Path $prerenderManifest) {
    Write-Host "Cache .next de build de produção detectado - limpando antes do dev server..."
    Remove-Item -Recurse -Force (Join-Path $projectRoot ".next")
}

# 4. Frontend em nova janela
Write-Host "Abrindo o frontend (npm run dev) em nova janela..."
Start-Process powershell -ArgumentList @(
    "-NoExit", "-Command",
    "cd '$projectRoot'; npm run dev"
)

Write-Host ""
Write-Host "Tudo iniciado! Em alguns segundos, abra http://localhost:3000"
