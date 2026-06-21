#Requires -Version 5.1
<#
.SYNOPSIS
    pcx-ai-toolkit setup for Windows 10 / 11 (native PowerShell).
.DESCRIPTION
    Clones and builds the LSP servers, installs AI skills to Claude Code if present.
.PARAMETER Project
    Optional path to a PCX scripting project; copies rules/CLAUDE.md into it.
.EXAMPLE
    .\setup.ps1
    .\setup.ps1 -Project C:\dev\my-pcx-project
#>
param(
    [string]$Project = ""
)

$ErrorActionPreference = "Stop"
$ToolkitDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "pcx-ai-toolkit setup (Windows)"
Write-Host "Location: $ToolkitDir"
Write-Host ""

# --- Check node / npm ---
function Test-Command($name) {
    return [bool](Get-Command $name -ErrorAction SilentlyContinue)
}

if (-not (Test-Command "node") -or -not (Test-Command "npm")) {
    Write-Host "ERROR: node and npm are required for LSP servers." -ForegroundColor Red
    Write-Host "Install Node.js 18+ from https://nodejs.org/"
    exit 1
}
if (-not (Test-Command "git")) {
    Write-Host "ERROR: git is required." -ForegroundColor Red
    Write-Host "Install Git from https://git-scm.com/"
    exit 1
}
$nodeVer = (node --version)
$npmVer  = (npm --version)
Write-Host "[ok] node $nodeVer, npm $npmVer"

# --- Run core setup logic via python ---
$py = Get-Command python3, python -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $py) {
    Write-Error "ERROR: Python 3.10+ is required but not found on PATH."
    exit 1
}

$coreScript = Join-Path $ToolkitDir "tools\setup-core.py"
if ($Project -ne "") {
    & $py.Source $coreScript --project $Project
} else {
    & $py.Source $coreScript
}

# --- Add tools to PATH ---
$toolsDir = Join-Path $ToolkitDir "tools"
$currentPath = [Environment]::GetEnvironmentVariable("PATH", "User")
if ($currentPath -split ';' -notcontains $toolsDir) {
    $newPath = "$currentPath;$toolsDir"
    [Environment]::SetEnvironmentVariable("PATH", $newPath, "User")
    Write-Host "[ok] Added $toolsDir to user Environment PATH" -ForegroundColor Green
    Write-Host "     Restart your terminal for PATH changes to take effect."
} else {
    Write-Host "[ok] pcx tools directory already in User PATH"
}
# --- Record installed version ---
$versionFile = Join-Path $ToolkitDir "VERSION"
$toolkitVersion = if (Test-Path $versionFile) { (Get-Content $versionFile -Raw).Trim() } else { "unknown" }
Write-Host "Version: $toolkitVersion"
$docCount = (Get-ChildItem -Path (Join-Path $ToolkitDir "docs") -Recurse -Filter *.md).Count
Write-Host ""
Write-Host "Setup complete."
Write-Host ""
Write-Host "Documentation:  $ToolkitDir\docs\ ($docCount files)"
Write-Host "Knowledge base: $ToolkitDir\knowledge\"
Write-Host "Skills:         $ToolkitDir\.claude\skills\"
Write-Host "MCP config:     $ToolkitDir\mcp\"
Write-Host "Templates:      $ToolkitDir\templates\"
Write-Host ""
Write-Host "Quick start:"
Write-Host "  1. Copy rules\CLAUDE.md to your PCX scripting project"
Write-Host "  2. Start coding - the AI reads docs automatically"
Write-Host "  3. See mcp\claude-code-setup.md for full integration"
