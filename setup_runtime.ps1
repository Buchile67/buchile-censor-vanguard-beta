[CmdletBinding()]
param(
    [ValidateSet("basic", "vanguard")]
    [string]$Edition = "vanguard"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

$installerName = "Miniconda3-py312_26.5.3-2-Windows-x86_64.exe"
$installerUrl = "https://repo.anaconda.com/miniconda/$installerName"
$installerSha256 = "75E829B26BD7B33B1DCE118639B8F39E561A6EBAA3B593B633D7445DD1A2D65A"

function Write-Step([string]$Message) {
    Write-Host ""
    Write-Host "[Buchile] $Message" -ForegroundColor Cyan
}

function Invoke-Native {
    param(
        [string]$FilePath,
        [string[]]$Arguments,
        [string]$Description
    )
    & $FilePath @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$Description failed with exit code $LASTEXITCODE."
    }
}

function Test-Installer([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        return $false
    }
    $actual = (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash
    return $actual -eq $installerSha256
}

try {
    if (-not [Environment]::Is64BitOperatingSystem) {
        throw "A 64-bit Windows installation is required."
    }

    # PSScriptRoot is already an absolute filesystem path and avoids command-line
    # quoting issues caused by a caller passing a directory ending in a backslash.
    $appRootPath = $PSScriptRoot
    $localAppData = [Environment]::GetFolderPath("LocalApplicationData")
    if ([string]::IsNullOrWhiteSpace($localAppData)) {
        $runtimeRoot = Join-Path $appRootPath ".runtime"
    } else {
        $runtimeRoot = Join-Path $localAppData "BuchileRuntime"
    }

    $minicondaRoot = Join-Path $runtimeRoot "miniconda"
    $condaExe = Join-Path $minicondaRoot "Scripts\conda.exe"
    $environmentName = if ($Edition -eq "vanguard") { "vanguard-beta" } else { "buchile-censor" }
    $environmentRoot = Join-Path $runtimeRoot "envs\$environmentName"
    $pythonExe = Join-Path $environmentRoot "python.exe"
    $readyMarker = Join-Path $environmentRoot ".buchile-ready"
    $bundledInstaller = Join-Path $appRootPath "installer\$installerName"
    $downloadedInstaller = Join-Path ([IO.Path]::GetTempPath()) "Buchile-$installerName"

    New-Item -ItemType Directory -Path $runtimeRoot -Force | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $runtimeRoot "envs") -Force | Out-Null

    if (-not (Test-Path -LiteralPath $condaExe -PathType Leaf)) {
        Write-Step "Preparing the private Miniconda runtime (one-time setup)."

        if (Test-Path -LiteralPath $bundledInstaller -PathType Leaf) {
            Write-Host "Using the Miniconda installer included in this package."
            $installerPath = $bundledInstaller
        } else {
            Write-Host "The bundled installer is not present; downloading the verified official installer."
            if (-not (Test-Installer $downloadedInstaller)) {
                [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
                try {
                    Invoke-WebRequest -UseBasicParsing -Uri $installerUrl -OutFile $downloadedInstaller
                } catch {
                    $curl = Get-Command "curl.exe" -ErrorAction SilentlyContinue
                    if (-not $curl) {
                        throw
                    }
                    Invoke-Native $curl.Source @("-L", "--fail", "--retry", "3", "--output", $downloadedInstaller, $installerUrl) "Miniconda download"
                }
            }
            $installerPath = $downloadedInstaller
        }

        if (-not (Test-Installer $installerPath)) {
            throw "The Miniconda installer is incomplete or its SHA-256 does not match. Please download the package again."
        }

        Write-Host "Miniconda is provided by Anaconda, Inc. and remains under its own license."
        Write-Host "License: https://www.anaconda.com/legal/terms/miniconda"
        $answer = Read-Host "输入 Y 并回车以安装私有运行环境 / Type Y and press Enter to continue"
        if ($answer -notmatch "^[Yy]$") {
            throw "Installation was cancelled by the user."
        }

        if (Test-Path -LiteralPath $minicondaRoot) {
            $backup = "$minicondaRoot.incomplete-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
            Move-Item -LiteralPath $minicondaRoot -Destination $backup
            Write-Host "An incomplete runtime was preserved at: $backup"
        }

        $installArguments = @(
            "/InstallationType=JustMe",
            "/RegisterPython=0",
            "/AddToPath=0",
            "/S",
            "/D=$minicondaRoot"
        )
        $process = Start-Process -FilePath $installerPath -ArgumentList $installArguments -Wait -PassThru
        if ($process.ExitCode -ne 0) {
            throw "Miniconda installer failed with exit code $($process.ExitCode)."
        }
        if (-not (Test-Path -LiteralPath $condaExe -PathType Leaf)) {
            throw "Miniconda finished but conda.exe was not created. Security software may have blocked the installation."
        }
    } else {
        Write-Step "Using the existing private Miniconda runtime."
    }

    if (-not (Test-Path -LiteralPath $pythonExe -PathType Leaf)) {
        Write-Step "Creating the isolated $environmentName environment."
        if (Test-Path -LiteralPath $environmentRoot) {
            $backup = "$environmentRoot.incomplete-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
            Move-Item -LiteralPath $environmentRoot -Destination $backup
            Write-Host "An incomplete environment was preserved at: $backup"
        }
        $env:CONDA_NO_PLUGINS = "true"
        Invoke-Native $condaExe @(
            "create",
            "--solver", "classic",
            "--override-channels",
            "--channel", "conda-forge",
            "--prefix", $environmentRoot,
            "python=3.12",
            "pip",
            "-y"
        ) "Conda environment creation"
    } else {
        Write-Step "The isolated $environmentName environment already exists."
    }

    Write-Step "Installing application dependencies. This can take several minutes."
    Invoke-Native $pythonExe @(
        "-m", "pip", "install",
        "--disable-pip-version-check",
        "--retries", "5",
        "--timeout", "90",
        "--upgrade", "pip"
    ) "pip upgrade"

    if ($Edition -eq "vanguard") {
        $samSetup = Join-Path $appRootPath "vendor\sam2\setup.py"
        if (-not (Test-Path -LiteralPath $samSetup -PathType Leaf)) {
            throw "SAM2 source is missing. Download the complete release package or clone with --recurse-submodules."
        }
        Invoke-Native $pythonExe @(
            "-m", "pip", "install",
            "--disable-pip-version-check",
            "--retries", "5",
            "--timeout", "90",
            "torch", "torchvision",
            "--index-url", "https://download.pytorch.org/whl/cu130"
        ) "PyTorch installation"
    }

    Invoke-Native $pythonExe @(
        "-m", "pip", "install",
        "--disable-pip-version-check",
        "--retries", "5",
        "--timeout", "90",
        "-r", (Join-Path $appRootPath "requirements.txt")
    ) "Application dependency installation"

    if ($Edition -eq "vanguard") {
        $env:SAM2_BUILD_CUDA = "0"
        Invoke-Native $pythonExe @(
            "-m", "pip", "install",
            "--disable-pip-version-check",
            "-e", (Join-Path $appRootPath "vendor\sam2")
        ) "SAM2 installation"
    }

    Set-Content -LiteralPath $readyMarker -Value "Buchile runtime ready" -Encoding ASCII
    Write-Step "Setup complete. The application will start automatically."
    Write-Host "Runtime: $minicondaRoot"
    Write-Host "Environment: $environmentRoot"
    exit 0
} catch {
    Write-Host ""
    Write-Host "[Buchile] Setup stopped: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "No existing Buchile environment was overwritten."
    Write-Host "If the problem continues, copy this entire window when requesting help."
    exit 1
}
