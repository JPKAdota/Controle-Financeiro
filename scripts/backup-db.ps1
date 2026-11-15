<#
.SYNOPSIS
    Gera um dump do Postgres local do Controle Financeiro em backups/.

.DESCRIPTION
    Roda `pg_dump` dentro do container `controle-financeiro-db` (via docker exec)
    e salva o resultado em backups/controle_financeiro_<timestamp>.sql.
    Mantém apenas os 30 backups mais recentes para não acumular espaço em disco.

.EXAMPLE
    .\scripts\backup-db.ps1
#>

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$backupDir = Join-Path $projectRoot "backups"
if (-not (Test-Path $backupDir)) {
    New-Item -ItemType Directory -Path $backupDir | Out-Null
}

$containerRunning = & docker ps --filter "name=controle-financeiro-db" --filter "status=running" --format "{{.Names}}"
if (-not $containerRunning) {
    Write-Error "O container 'controle-financeiro-db' não está rodando. Rode 'docker compose up -d' primeiro."
    exit 1
}

$timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$backupFile = Join-Path $backupDir "controle_financeiro_$timestamp.sql"

Write-Host "Gerando backup em $backupFile ..."
docker exec controle-financeiro-db pg_dump -U postgres controle_financeiro | Out-File -FilePath $backupFile -Encoding utf8

if ((Get-Item $backupFile).Length -eq 0) {
    Write-Error "O backup ficou vazio - algo deu errado no pg_dump."
    Remove-Item $backupFile -Force
    exit 1
}

Write-Host "Backup concluído: $backupFile"

# Mantém só os 30 backups mais recentes
$antigos = Get-ChildItem $backupDir -Filter "controle_financeiro_*.sql" |
    Sort-Object LastWriteTime -Descending |
    Select-Object -Skip 30

if ($antigos) {
    Write-Host "Removendo $($antigos.Count) backup(s) antigo(s) além dos 30 mais recentes..."
    $antigos | Remove-Item -Force
}
