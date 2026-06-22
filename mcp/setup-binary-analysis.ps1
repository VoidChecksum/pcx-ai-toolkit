#Requires -Version 5.1
<#
.SYNOPSIS
    MCP-only setup — use if the analysis suite is already installed.
    For a fresh install (suite + MCP), use installers\install.ps1 instead.
.PARAMETER InstallDir
    Path to the existing installation. Auto-detected if omitted.
.PARAMETER SkipPkg
    Skip downloading the MCP package (already installed).
.PARAMETER SkipActivate
    Skip idalib activation.
#>
param(
    [string]$InstallDir   = "",
    [switch]$SkipPkg,
    [switch]$SkipActivate
)
$ErrorActionPreference = "Stop"

Write-Host "Binary analysis MCP setup — suite already installed (Windows)"
Write-Host ""

function Find-InstallDir {
    if ($env:IDADIR -and (Test-Path "$env:IDADIR\ida.hlp")) { return $env:IDADIR }
    $cfgDir = if ($env:IDAUSR) { $env:IDAUSR } else { Join-Path $env:APPDATA "Hex-Rays\IDA Pro" }
    $cfg    = Join-Path $cfgDir "ida-config.json"
    if (Test-Path $cfg) {
        try {
            $d = Get-Content $cfg | ConvertFrom-Json
            $dir = $d.Paths.'ida-install-dir'
            if ($dir -and (Test-Path "$dir\ida.hlp")) { return $dir }
        } catch {}
    }
    $candidates = @(
        "C:\Program Files\IDA Professional 9.3",
        "C:\Program Files\IDA Professional 9.2",
        "C:\Program Files\IDA Pro 9.3",
        "C:\Program Files\IDA Pro 9.2"
    )
    foreach ($c in $candidates) { if (Test-Path "$c\ida.hlp") { return $c } }
    return ""
}

# ── uv ────────────────────────────────────────────────────────────────────────
if (Get-Command "uv" -ErrorAction SilentlyContinue) {
    Write-Host "[ok] uv $(uv --version 2>$null | Select-Object -First 1)"
} else {
    Write-Host "[..] Installing uv..."
    $tmp = Join-Path $env:TEMP "uv-installer.ps1"
    Invoke-WebRequest "https://astral.sh/uv/install.ps1" -OutFile $tmp -UseBasicParsing
    & powershell -ExecutionPolicy Bypass -File $tmp
    Remove-Item $tmp -Force -ErrorAction SilentlyContinue
    $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH","User") + ";" + $env:PATH
    if (-not (Get-Command "uv" -ErrorAction SilentlyContinue)) {
        Write-Host "[!!] uv install failed."; exit 1
    }
    Write-Host "[ok] uv installed"
}

# ── Python 3.11+ ──────────────────────────────────────────────────────────────
$PYTHON = $null
foreach ($py in @("python", "python3")) {
    if (Get-Command $py -ErrorAction SilentlyContinue) {
        $ver = & $py -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
        if ($ver) {
            $p = $ver.Split(".")
            if ([int]$p[0] -ge 3 -and [int]$p[1] -ge 11) {
                $PYTHON = $py; Write-Host "[ok] Python $ver ($py)"; break
            }
        }
    }
}
if (-not $PYTHON) {
    Write-Host "[..] Python 3.11+ not found — installing via uv..."
    uv python install 3.12; $PYTHON = "python"
    Write-Host "[ok] Python installed via uv"
}

# ── ida-pro-mcp package ───────────────────────────────────────────────────────
if ($SkipPkg) {
    Write-Host "[--] Skipping package install (-SkipPkg)"
} elseif ((uv tool list 2>$null) | Select-String "ida-pro-mcp") {
    Write-Host "[ok] ida-pro-mcp already installed  (upgrade: uv tool upgrade ida-pro-mcp)"
} else {
    Write-Host "[..] Installing ida-pro-mcp..."
    uv tool install ida-pro-mcp
    Write-Host "[ok] ida-pro-mcp installed"
}

# ── find installation directory ───────────────────────────────────────────────
if (-not $SkipActivate) {
    if (-not $InstallDir) { $InstallDir = Find-InstallDir }
    if ($InstallDir -and (Test-Path "$InstallDir\ida.hlp")) {
        Write-Host "[ok] Found installation: $InstallDir"
    } elseif ($InstallDir) {
        Write-Host "[!!] Path doesn't look like a valid installation: $InstallDir"; exit 1
    } else {
        Write-Host "[!!] Could not auto-detect installation. Re-run with -InstallDir 'C:\...'."
        Write-Host "     Skipping activation."
        $SkipActivate = $true
    }
}

# ── activate idalib ───────────────────────────────────────────────────────────
if (-not $SkipActivate -and $InstallDir) {
    $act = Join-Path $InstallDir "idalib\python\py-activate-idalib.py"
    if (Test-Path $act) {
        Write-Host "[..] Activating idalib bindings..."
        uv run $act --ida-install-dir $InstallDir
        Write-Host "[ok] idalib activated"
    } else {
        Write-Host "[!!] Activation script not found: $act"
    }
    $whl = Get-ChildItem "$InstallDir\idalib\python\idapro*.whl" -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($whl) {
        $ok = & $PYTHON -c "import idapro" 2>$null; $r = $LASTEXITCODE
        if ($r -ne 0) {
            & $PYTHON -m pip install --quiet $whl.FullName
            Write-Host "[ok] idapro wheel installed"
        } else { Write-Host "[ok] idapro already importable" }
    }
}

# ── Claude Code MCP config ────────────────────────────────────────────────────
$ClaudeDir = Join-Path $env:USERPROFILE ".claude"
if (Test-Path $ClaudeDir) {
    $McpCfg = Join-Path $ClaudeDir "mcp.json"
    Write-Host "[..] Configuring Claude Code MCP..."
    $cfg = @{}
    if (Test-Path $McpCfg) { try { $cfg = Get-Content $McpCfg | ConvertFrom-Json } catch {} }
    if (-not $cfg.mcpServers) {
        $cfg | Add-Member -NotePropertyName "mcpServers" -NotePropertyValue @{} -Force
    }
    $entry = @{ command = "uvx"; args = @("idalib-mcp", "--stdio") }
    if (-not $SkipActivate -and $InstallDir) { $entry["env"] = @{ IDADIR = $InstallDir } }
    $cfg.mcpServers | Add-Member -NotePropertyName "binary-analysis" -NotePropertyValue $entry -Force
    $cfg | ConvertTo-Json -Depth 10 | Set-Content $McpCfg -Encoding UTF8
    Write-Host "[ok] MCP config written to $McpCfg"
    Write-Host "     Restart Claude Code to pick up the change."
} else {
    Write-Host "[--] Claude Code not detected — add manually:"
    Write-Host '     "binary-analysis": { "command": "uvx", "args": ["idalib-mcp", "--stdio"] }'
}

Write-Host ""
Write-Host "Done.  Run: uvx idalib-mcp --stdio"
Write-Host "Upgrade:    uv tool upgrade ida-pro-mcp"
