<#
.SYNOPSIS
    Restaura o Postgres local do Controle Financeiro a partir de um dump gerado por backup-db.ps1.

.DESCRIPTION
    APAGA os dados atuais do banco e restaura a partir do arquivo .sql informado.
    Pede confirmação explícita antes de prosseguir.

.PARAMETER BackupFile
    Caminho do arquivo .sql a restaurar (ex: backups\controle_financeiro_2026-09-07_10-00-00.sql).

.EXAMPLE
    .\scripts\restore-db.ps1 -BackupFile .\backups\controle_financeiro_2026-09-07_10-00-00.sql
#>

param(
    [Parameter(Mandatory = $true)]
    [string]$BackupFile
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $BackupFile)) {
    Write-Error "Arquivo de backup não encontrado: $BackupFile"
    exit 1
}

$containerRunning = & docker ps --filter "name=controle-financeiro-db" --filter "status=running" --format "{{.Names}}"
if (-not $containerRunning) {
    Write-Error "O container 'controle-financeiro-db' não está rodando. Rode 'docker compose up -d' primeiro."
    exit 1
}

Write-Warning "Isso vai APAGAR todos os dados atuais do banco 'controle_financeiro' e substituir pelo conteúdo de:`n  $BackupFile"
$confirm = Read-Host "Digite 'sim' para confirmar"
if ($confirm -ne "sim") {
    Write-Host "Cancelado."
    exit 0
}

Write-Host "Zerando o schema atual..."
docker exec controle-financeiro-db psql -U postgres -d controle_financeiro -c "drop schema public cascade; create schema public;"

Write-Host "Restaurando a partir de $BackupFile ..."
Get-Content $BackupFile | docker exec -i controle-financeiro-db psql -U postgres -d controle_financeiro

Write-Host "Restauração concluída."
