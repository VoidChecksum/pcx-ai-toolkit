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

# --- Clone + build an LSP server ---
function Install-Lsp($name, $url, $outFile) {
    $dir = Join-Path $ToolkitDir "lsp\$name"
    if (-not (Test-Path (Join-Path $dir ".git"))) {
        Write-Host "[..] Cloning $name..."
        git clone --depth 1 $url $dir
    } else {
        Write-Host "[ok] $name already present"
    }
    Write-Host "[..] Building $name..."
    Push-Location $dir
    try {
        # npm on Windows is npm.cmd; call via cmd to avoid PSReadLine quirks
        & npm install 2>&1 | Out-Null
        & npm run compile 2>&1 | Out-Null
    } finally {
        Pop-Location
    }
    $built = Join-Path $dir $outFile
    if (Test-Path $built) {
        Write-Host "[ok] $name built: $outFile"
    } else {
        Write-Host "[!!] $name build did not produce $outFile — run 'npm run compile' in $dir manually" -ForegroundColor Yellow
    }
}

Install-Lsp "enma-lsp"      "https://github.com/sinnafuls/enma-lsp.git"      "server\dist\server.js"
Install-Lsp "angel-lsp-pcx" "https://github.com/sinnafuls/angel-lsp-pcx.git" "server\out\server.js"

# --- Install skills to Claude Code if present ---
$claudeDir = Join-Path $env:USERPROFILE ".claude"
if (Test-Path $claudeDir) {
    Write-Host ""
    Write-Host "[..] Claude Code detected - installing skills..."
    foreach ($skillDir in Get-ChildItem (Join-Path $ToolkitDir ".claude\skills") -Directory) {
        $src = Join-Path $skillDir.FullName "SKILL.md"
        if (-not (Test-Path $src)) { continue }
        $dest = Join-Path $claudeDir "skills\$($skillDir.Name)"
        New-Item -ItemType Directory -Force -Path $dest | Out-Null
        Copy-Item $src $dest -Force
    }
    Write-Host "[ok] Skills installed to $claudeDir\skills\"
} else {
    Write-Host ""
    Write-Host "[--] Claude Code not detected - skip skill install."
    Write-Host "     Manual: copy .claude\skills\* to $claudeDir\skills\"
}

# --- Optional: copy CLAUDE.md to a project ---
if ($Project -ne "") {
    if (Test-Path $Project) {
        Copy-Item (Join-Path $ToolkitDir "rules\CLAUDE.md") (Join-Path $Project "CLAUDE.md") -Force
        Write-Host "[ok] Project rules copied to $Project\CLAUDE.md"
    } else {
        Write-Host "[!!] Project path not found: $Project" -ForegroundColor Yellow
    }
}

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
