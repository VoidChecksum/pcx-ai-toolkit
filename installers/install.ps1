#Requires -Version 5.1
<#
.SYNOPSIS
    Full Windows setup: installs the analysis suite permanently, patches it,
    activates idalib, installs the binary analysis MCP server, configures Claude Code.
.PARAMETER Prefix
    Installation directory. Default: "C:\Program Files\IDA Professional 9.3"
.PARAMETER SkipMcp
    Skip MCP server install.
.EXAMPLE
    .\installers\install.ps1
    .\installers\install.ps1 -Prefix "D:\tools\ida"
    .\installers\install.ps1 -SkipMcp
#>
param(
    [string]$Prefix = "C:\Program Files\IDA Professional 9.3",
    [switch]$SkipMcp
)
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Installer = Join-Path $ScriptDir "ida-pro_93_x64win.exe"
$Keygen    = Join-Path $ScriptDir "keygen.js"
$PatchDir  = Join-Path $ScriptDir "kg_patch\win"

Write-Host "Analysis suite installer (Windows)"
Write-Host ""

# ── check LFS files present and real ─────────────────────────────────────────
foreach ($f in @($Installer, $Keygen, "$PatchDir\ida.dll", "$PatchDir\ida32.dll")) {
    if (-not (Test-Path $f)) {
        Write-Host "[!!] Missing: $f"
        Write-Host "     Run: git lfs pull"
        exit 1
    }
    if ((Get-Item $f).Length -lt 1MB) {
        Write-Host "[!!] $f looks like a Git LFS pointer, not the real file."
        Write-Host "     Run: git lfs pull"
        exit 1
    }
}

# ── Node.js ───────────────────────────────────────────────────────────────────
if (-not (Get-Command "node" -ErrorAction SilentlyContinue)) {
    Write-Host "[!!] Node.js required. Install from https://nodejs.org/ then re-run."
    exit 1
}
Write-Host "[ok] node $(node --version)"

# ── step 1: silent install ────────────────────────────────────────────────────
Write-Host "[..] Running installer to: $Prefix (takes a minute)..."
$proc = Start-Process -FilePath $Installer `
    -ArgumentList @("--mode", "unattended", "--prefix", $Prefix) `
    -Wait -PassThru
if ($proc.ExitCode -ne 0) {
    Write-Host "[!!] Installer exited with code $($proc.ExitCode)"
    exit 1
}
Write-Host "[ok] Installed to: $Prefix"

# ── step 2: replace DLLs with pre-patched versions ───────────────────────────
Write-Host "[..] Patching DLLs..."
foreach ($dll in @("ida.dll", "ida32.dll")) {
    $dst = Join-Path $Prefix $dll
    if (-not (Test-Path $dst)) {
        Write-Host "[!!] Expected DLL not found: $dst"
        exit 1
    }
    Copy-Item -Path (Join-Path $PatchDir $dll) -Destination $dst -Force
    Write-Host "    patched: $dll"
}

# ── step 3: generate license ──────────────────────────────────────────────────
Write-Host "[..] Generating license..."
Push-Location $Prefix
& node $Keygen
Pop-Location

$LicFile = Join-Path $Prefix "idapro.hexlic"
if (-not (Test-Path $LicFile)) {
    Write-Host "[!!] License file not generated: $LicFile"
    exit 1
}
Write-Host "[ok] License written: $LicFile"

# ── step 4: uv ────────────────────────────────────────────────────────────────
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
        Write-Host "[!!] uv install failed. See https://docs.astral.sh/uv/"
        exit 1
    }
    Write-Host "[ok] uv installed"
}

# ── step 5: Python 3.11+ ──────────────────────────────────────────────────────
$PYTHON = $null
foreach ($py in @("python", "python3")) {
    if (Get-Command $py -ErrorAction SilentlyContinue) {
        $ver = & $py -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
        if ($ver) {
            $p = $ver.Split("."); if ([int]$p[0] -ge 3 -and [int]$p[1] -ge 11) {
                $PYTHON = $py; Write-Host "[ok] Python $ver ($py)"; break
            }
        }
    }
}
if (-not $PYTHON) {
    Write-Host "[..] Python 3.11+ not found — installing via uv..."
    uv python install 3.12
    $PYTHON = "python"
    Write-Host "[ok] Python installed via uv"
}

# ── step 6: activate idalib ───────────────────────────────────────────────────
Write-Host "[..] Activating idalib Python bindings..."
$ActivateScript = Join-Path $Prefix "idalib\python\py-activate-idalib.py"
if (Test-Path $ActivateScript) {
    uv run $ActivateScript --ida-install-dir $Prefix
    Write-Host "[ok] idalib activated"
} else {
    Write-Host "[!!] Activation script not found: $ActivateScript"
}

$Wheel = Get-ChildItem "$Prefix\idalib\python\idapro*.whl" -ErrorAction SilentlyContinue | Select-Object -First 1
if ($Wheel) {
    $ok = & $PYTHON -c "import idapro" 2>$null; $r = $LASTEXITCODE
    if ($r -ne 0) {
        & $PYTHON -m pip install --quiet $Wheel.FullName
        Write-Host "[ok] idapro wheel installed"
    } else {
        Write-Host "[ok] idapro already importable"
    }
}

# ── step 7: MCP server ────────────────────────────────────────────────────────
if (-not $SkipMcp) {
    if ((uv tool list 2>$null) | Select-String "ida-pro-mcp") {
        Write-Host "[ok] ida-pro-mcp already installed"
    } else {
        Write-Host "[..] Installing binary analysis MCP server..."
        uv tool install ida-pro-mcp
        Write-Host "[ok] ida-pro-mcp installed"
    }

    $ClaudeDir = Join-Path $env:USERPROFILE ".claude"
    if (Test-Path $ClaudeDir) {
        $McpCfg = Join-Path $ClaudeDir "mcp.json"
        Write-Host "[..] Configuring Claude Code MCP..."
        $cfg = @{}
        if (Test-Path $McpCfg) {
            try { $cfg = Get-Content $McpCfg | ConvertFrom-Json } catch {}
        }
        if (-not $cfg.mcpServers) {
            $cfg | Add-Member -NotePropertyName "mcpServers" -NotePropertyValue @{} -Force
        }
        $cfg.mcpServers | Add-Member -NotePropertyName "binary-analysis" -NotePropertyValue @{
            command = "uvx"
            args    = @("idalib-mcp", "--stdio")
            env     = @{ IDADIR = $Prefix }
        } -Force
        $cfg | ConvertTo-Json -Depth 10 | Set-Content $McpCfg -Encoding UTF8
        Write-Host "[ok] MCP config written to $McpCfg"
        Write-Host "     Restart Claude Code to pick up the change."
    } else {
        Write-Host "[--] Claude Code not detected — skipping MCP config."
        Write-Host '     Add to your MCP client config manually:'
        Write-Host '       "binary-analysis": {'
        Write-Host '         "command": "uvx",'
        Write-Host '         "args": ["idalib-mcp", "--stdio"],'
        Write-Host "         `"env`": { `"IDADIR`": `"$Prefix`" }"
        Write-Host '       }'
    }
}

# ── done ──────────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "Done."
Write-Host "  Installed to : $Prefix"
Write-Host "  License      : $Prefix\idapro.hexlic"
if (-not $SkipMcp) { Write-Host "  MCP (headless): uvx idalib-mcp --stdio" }
Write-Host "  MCP (GUI plugin, optional): pip install ida-pro-mcp; ida-pro-mcp --install"
Write-Host "  Upgrade later: uv tool upgrade ida-pro-mcp"
