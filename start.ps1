[CmdletBinding()]
param(
    [string]$BindAddress = "127.0.0.1",

    [ValidateRange(1, 65535)]
    [int]$Port = 8000,

    [switch]$SkipSync,
    [switch]$SkipChecks,
    [switch]$SkipMigrations,
    [switch]$NoReload
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Invoke-Uv {
    param(
        [Parameter(Mandatory)]
        [string[]]$Arguments
    )

    & uv @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "O comando 'uv $($Arguments -join ' ')' terminou com o codigo $LASTEXITCODE."
    }
}

$projectRoot = $PSScriptRoot
$envFile = Join-Path $projectRoot ".env"
$envTemplate = Join-Path $projectRoot ".env-contrib"

Push-Location $projectRoot
try {
    if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
        throw "UV nao encontrado. Instale-o em https://docs.astral.sh/uv/getting-started/installation/ e execute este script novamente."
    }

    if (-not (Test-Path -LiteralPath "pyproject.toml")) {
        throw "pyproject.toml nao encontrado em '$projectRoot'."
    }

    if (-not (Test-Path -LiteralPath $envFile)) {
        if (-not (Test-Path -LiteralPath $envTemplate)) {
            throw "Arquivo .env ausente e modelo .env-contrib nao encontrado."
        }

        Copy-Item -LiteralPath $envTemplate -Destination $envFile
        Write-Host "Arquivo .env criado a partir de .env-contrib." -ForegroundColor Yellow
        Write-Host "Revise os valores antes de usar a aplicacao fora do ambiente local." -ForegroundColor Yellow
    }

    Write-Host "UV: $(& uv --version)" -ForegroundColor Cyan

    if (-not $SkipSync) {
        Write-Host "Sincronizando Python e dependencias pelo uv.lock..." -ForegroundColor Cyan
        Invoke-Uv -Arguments @("sync", "--locked")
    }

    if (-not $SkipChecks) {
        Write-Host "Validando a configuracao do Django..." -ForegroundColor Cyan
        Invoke-Uv -Arguments @("run", "--no-sync", "python", "manage.py", "check")
    }

    if (-not $SkipMigrations) {
        Write-Host "Aplicando migracoes pendentes..." -ForegroundColor Cyan
        Invoke-Uv -Arguments @("run", "--no-sync", "python", "manage.py", "migrate", "--noinput")
    }

    $serverAddress = "${BindAddress}:$Port"
    $runServerArguments = @("run", "--no-sync", "python", "manage.py", "runserver", $serverAddress)
    if ($NoReload) {
        $runServerArguments += "--noreload"
    }

    Write-Host "Iniciando Orcamento Pessoal em http://$serverAddress" -ForegroundColor Green
    Write-Host "Pressione Ctrl+C para encerrar." -ForegroundColor DarkGray
    Invoke-Uv -Arguments $runServerArguments
}
finally {
    Pop-Location
}
