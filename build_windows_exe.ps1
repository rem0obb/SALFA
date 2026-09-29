$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

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
Invoke-Python $python -m PyInstaller --clean --noconfirm --onefile --windowed `
    --optimize 2 --name SALFAGenerator ctf_generator_gui.py

$exePath = Join-Path $PSScriptRoot "dist\SALFAGenerator.exe"
if (-not (Test-Path $exePath)) {
    throw "Build finished, but $exePath was not created."
}
if ((Get-Item $exePath).Length -lt 1MB) {
    throw "The generated executable is unexpectedly small and may be incomplete."
}

$check = Start-Process -FilePath $exePath -ArgumentList "--self-test" -Wait -PassThru
if ($check.ExitCode -ne 0) {
    throw "The executable self-test failed with exit code $($check.ExitCode)."
}

Write-Host "Built and verified: $exePath"
