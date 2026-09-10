$ErrorActionPreference = "Stop"

Write-Host "========================================"
Write-Host "        SHOP INSTALLER"
Write-Host "========================================"
Write-Host ""

$InstallDir = $PSScriptRoot
$PayloadDir = Join-Path $InstallDir "payload"

Write-Host "Install directory:"
Write-Host $InstallDir
Write-Host ""

# --------------------------------------------------
# 1. Check Docker
# --------------------------------------------------

Write-Host "[1/7] Checking Docker..."

try {
    docker version | Out-Null
}
catch {
    Write-Host ""
    Write-Host "ERROR: Docker is not available." -ForegroundColor Red
    Write-Host "Please install and start Docker Desktop first."
    exit 1
}

Write-Host "Docker is available." -ForegroundColor Green


# --------------------------------------------------
# 2. Check required files
# --------------------------------------------------

Write-Host ""
Write-Host "[2/7] Checking installer files..."

$RequiredFiles = @(
    "postgres-16.tar",
    "shop-backend-1.0.4.tar",
    "docker-compose.yml",
    ".env.template"
)

foreach ($File in $RequiredFiles) {

    $Path = Join-Path $PayloadDir $File

    if (-not (Test-Path $Path)) {
        Write-Host "ERROR: Missing file: $Path" -ForegroundColor Red
        exit 1
    }

    Write-Host "OK: $File" -ForegroundColor Green
}


# --------------------------------------------------
# 3. Load PostgreSQL image
# --------------------------------------------------

Write-Host ""
Write-Host "[3/7] Loading PostgreSQL Docker image..."

docker load -i (Join-Path $PayloadDir "postgres-16.tar")

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to load PostgreSQL image." -ForegroundColor Red
    exit 1
}

Write-Host "PostgreSQL image loaded." -ForegroundColor Green


# --------------------------------------------------
# 4. Load Shop image
# --------------------------------------------------

Write-Host ""
Write-Host "[4/7] Loading Shop Docker image..."

docker load -i (Join-Path $PayloadDir "shop-backend-1.0.4.tar")

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to load Shop image." -ForegroundColor Red
    exit 1
}

Write-Host "Shop image loaded." -ForegroundColor Green


# --------------------------------------------------
# 5. Create .env
# --------------------------------------------------

Write-Host ""
Write-Host "[5/7] Creating environment configuration..."

$EnvFile = Join-Path $InstallDir ".env"

if (-not (Test-Path $EnvFile)) {

    $EnvContent = @"
DB_NAME=shop_db
DB_USER=postgres
DB_PASSWORD=123456
DB_HOST=db
DB_PORT=5432

ADMIN_USERNAME=admin
ADMIN_PASSWORD=Admin123456!
ADMIN_EMAIL=admin@shop.local
"@

    Set-Content -Path $EnvFile -Value $EnvContent -Encoding UTF8

    Write-Host ".env created." -ForegroundColor Green
}
else {
    Write-Host ".env already exists. Keeping existing configuration." -ForegroundColor Yellow
}


# --------------------------------------------------
# 6. Start Shop
# --------------------------------------------------

Write-Host ""
Write-Host "[6/7] Starting Shop..."

$ComposeFile = Join-Path $PayloadDir "docker-compose.yml"
$EnvFile = Join-Path $InstallDir ".env"

Write-Host ""
Write-Host "[6/7] Starting Shop..."

docker compose `
    -f $ComposeFile `
    --env-file $EnvFile `
    up -d

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: docker compose up failed." -ForegroundColor Red
    exit 1
}

Write-Host "Docker containers started." -ForegroundColor Green


# --------------------------------------------------
# 7. Wait for Shop
# --------------------------------------------------

Write-Host ""
Write-Host "[7/7] Waiting for Shop..."

$MaxAttempts = 30
$Attempt = 0

while ($Attempt -lt $MaxAttempts) {

    $Attempt++

    try {

        $Response = Invoke-WebRequest `
            -Uri "http://localhost:8010/admin/login/" `
            -UseBasicParsing `
            -TimeoutSec 3

        if ($Response.StatusCode -ge 200 -and $Response.StatusCode -lt 500) {

            Write-Host ""
            Write-Host "========================================"
            Write-Host " SHOP INSTALLATION COMPLETED"
            Write-Host "========================================"
            Write-Host ""
            Write-Host "Shop is available at:"
            Write-Host "http://localhost:8010"
            Write-Host ""

            Start-Process "http://localhost:8010/admin/login/"

            exit 0
        }

    }
    catch {
        # Shop is not ready yet
    }

    Write-Host "Waiting... ($Attempt/$MaxAttempts)"
    Start-Sleep -Seconds 2
}

Write-Host ""
Write-Host "ERROR: Shop did not become available." -ForegroundColor Red
Write-Host ""
Write-Host "Docker status:"
docker compose `
    -f $ComposeFile `
    --env-file $EnvFile `
    ps

Write-Host ""
Write-Host "Web logs:"
docker compose `
    -f $ComposeFile `
    --env-file $EnvFile `
    logs web --tail 100

exit 1