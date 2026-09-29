$ErrorActionPreference = "Stop"
$sourceRoot = $PSScriptRoot

function Test-Python {
    param(
        [Parameter(Mandatory = $true)]
        [string] $Exe,
        [string[]] $PrefixArgs = @()
    )

    try {
        & $Exe @PrefixArgs -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" *> $null
        return $LASTEXITCODE -eq 0
    } catch {
        return $false
    }
}

function Find-Python {
    $commands = @(
        @{ Exe = "python"; Args = @() },
        @{ Exe = "python3"; Args = @() },
        @{ Exe = "py"; Args = @("-3") }
    )

    foreach ($candidate in $commands) {
        if ((Get-Command $candidate.Exe -ErrorAction SilentlyContinue) -and
            (Test-Python $candidate.Exe $candidate.Args)) {
            return [pscustomobject] $candidate
        }
    }

    $roots = @(
        "$env:LOCALAPPDATA\Programs\Python",
        "$env:ProgramFiles\Python",
        "${env:ProgramFiles(x86)}\Python"
    ) | Where-Object { $_ -and (Test-Path $_) }

    foreach ($root in $roots) {
        $matches = Get-ChildItem -Path $root -Filter python.exe -Recurse -ErrorAction SilentlyContinue |
            Sort-Object FullName -Descending
        foreach ($match in $matches) {
            if (Test-Python $match.FullName) {
                return [pscustomobject] @{ Exe = $match.FullName; Args = @() }
            }
        }
    }
    return $null
}

function Invoke-Python {
    param(
        [Parameter(Mandatory = $true)]
        [object] $Python,
        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]] $Args
    )

    & $Python.Exe @($Python.Args + $Args)
    if ($LASTEXITCODE -ne 0) {
        throw "Python failed with exit code $LASTEXITCODE"
    }
}

function Install-Python {
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        throw "Python 3.10+ was not found and winget is unavailable. Install Python from python.org and run this script again."
    }

    $packageIds = @(
        "Python.Python.3.14",
        "Python.Python.3.13",
        "Python.Python.3.12",
        "Python.Python.3.11",
        "Python.Python.3.10"
    )
    foreach ($packageId in $packageIds) {
        Write-Host "Installing $packageId with winget..."
        winget install --exact --id $packageId --source winget `
            --accept-package-agreements --accept-source-agreements --scope user
        if ($LASTEXITCODE -eq 0) {
            $python = Find-Python
            if ($python) { return $python }
        }
    }
    throw "Python installation did not complete."
}

$python = Find-Python
if (-not $python) { $python = Install-Python }
Write-Host "Using Python: $($python.Exe) $($python.Args -join ' ')"

try {
    Invoke-Python $python -m ensurepip --upgrade
} catch {
    Write-Host "ensurepip is unavailable; continuing with the installed pip."
}

Invoke-Python $python -c "import tkinter, pip"
Invoke-Python $python -m pip install --upgrade pip pyinstaller

# PyInstaller calls Win32 realpath APIs that can fail on mapped, network, or
# non-Windows volumes. Build entirely on the local system drive, then copy only
# the verified executable back to the project directory.
$buildRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("SALFAGenerator-build-" + [guid]::NewGuid().ToString("N"))
$localDist = Join-Path $buildRoot "dist"
$localExe = Join-Path $localDist "SALFAGenerator.exe"
$outputDir = Join-Path $sourceRoot "dist"
$exePath = Join-Path $outputDir "SALFAGenerator.exe"

New-Item -ItemType Directory -Path $buildRoot -Force | Out-Null
Write-Host "Local build directory: $buildRoot"

try {
    Copy-Item (Join-Path $sourceRoot "ctf_generator_gui.py") $buildRoot -Force
    Copy-Item (Join-Path $sourceRoot "flare_generator.py") $buildRoot -Force

    Push-Location $buildRoot
    try {
        Invoke-Python $python -m PyInstaller --clean --noconfirm --onefile --windowed `
            --optimize 2 --name SALFAGenerator ctf_generator_gui.py
    } finally {
        Pop-Location
    }

    if (-not (Test-Path $localExe)) {
        throw "Build finished, but $localExe was not created."
    }
    if ((Get-Item $localExe).Length -lt 1MB) {
        throw "The generated executable is unexpectedly small and may be incomplete."
    }

    $check = Start-Process -FilePath $localExe -ArgumentList "--self-test" -Wait -PassThru
    if ($check.ExitCode -ne 0) {
        throw "The executable self-test failed with exit code $($check.ExitCode)."
    }

    New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
    Copy-Item $localExe $exePath -Force
} finally {
    if (Test-Path $buildRoot) {
        Remove-Item $buildRoot -Recurse -Force
    }
}

Write-Host "Built and verified: $exePath"
