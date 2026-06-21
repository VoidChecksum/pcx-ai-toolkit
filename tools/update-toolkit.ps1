#Requires -Version 5.1
<#
.SYNOPSIS
    Self-update pcx-ai-toolkit from its git remote.
.DESCRIPTION
    Pulls the latest changes from origin/main, rebuilds LSP servers,
    refreshes AI skills, and regenerates the llms-* knowledge bundles
    if they have drifted from the source.
.PARAMETER Check
    Check only — report whether an update is available, exit 1 if needed.
.PARAMETER Force
    Force re-run of post-update hooks even if already up to date.
.PARAMETER SkipLsp
    Skip LSP server rebuild.
.PARAMETER SkipSkills
    Skip AI skill refresh.
.PARAMETER SkipBundles
    Skip knowledge bundle regeneration.
.EXAMPLE
    .\tools\update-toolkit.ps1
    .\tools\update-toolkit.ps1 -Check
    .\tools\update-toolkit.ps1 -Force -SkipLsp
#>
param(
    [switch]$Check,
    [switch]$Force,
    [switch]$SkipLsp,
    [switch]$SkipSkills,
    [switch]$SkipBundles
)

$ErrorActionPreference = "Stop"
$ToolkitDir = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)

Set-Location $ToolkitDir

# ── preflight ────────────────────────────────────────────────────────────────

$remoteUrl = git remote get-url origin 2>$null
if (-not $remoteUrl) {
    Write-Error "No git remote 'origin' found — cannot auto-update."
    exit 3
}

$currentRef = git rev-parse HEAD
$currentBranch = git rev-parse --abbrev-ref HEAD
$remoteBranch = "origin/main"

# Handle detached HEAD
if ($currentBranch -eq "HEAD") {
    Write-Host "Detached HEAD at $currentRef"
    Write-Host "Switching to main before updating..."
    git checkout main 2>$null
    if ($LASTEXITCODE -ne 0) { Write-Error "Could not checkout main"; exit 3 }
    $currentBranch = "main"
    $remoteBranch = "origin/main"
}

# ── fetch ────────────────────────────────────────────────────────────────────

Write-Host "Fetching from origin..."
git fetch origin 2>$null
if ($LASTEXITCODE -ne 0) { Write-Error "Fetch failed — check network"; exit 3 }

$remoteRef = git rev-parse $remoteBranch 2>$null
if (-not $remoteRef) { Write-Error "Could not resolve $remoteBranch"; exit 3 }

if ($currentRef -eq $remoteRef -and -not $Force) {
    if ($Check) {
        Write-Host "Up to date ($currentRef)"
        exit 0
    }
    Write-Host "Already up to date. Use -Force to re-run post-update hooks."
    exit 0
}

if ($Check) {
    $behind = git rev-list --count "HEAD..$remoteBranch" 2>$null
    $ahead = git rev-list --count "$remoteBranch..HEAD" 2>$null
    Write-Host "Update available: $behind commit(s) behind, $ahead commit(s) ahead"
    Write-Host "  local:  $currentRef"
    Write-Host "  remote: $remoteRef"
    exit 1
}

# ── safety: abort if local has uncommitted changes ──────────────────────────

$diff = git diff --quiet 2>$null
$diffCached = git diff --cached --quiet 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Error "Uncommitted changes detected — stash or commit before updating."
    exit 3
}

# ── update ───────────────────────────────────────────────────────────────────

Write-Host "Updating $currentBranch..."
$oldVersion = if (Test-Path "VERSION") { Get-Content VERSION -Raw } else { "unknown" }
$oldVersion = $oldVersion.Trim()

if ($Force -and $currentRef -eq $remoteRef) {
    Write-Host "Forced run — skipping git pull (already at latest)"
} else {
    git pull --ff-only origin $currentBranch 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Pull failed — local and remote have diverged.`nResolve manually: git pull --rebase origin $currentBranch"
        exit 3
    }
}

# Update submodules
git submodule update --init --recursive 2>$null | Out-Null

$newRef = git rev-parse HEAD
$newVersion = if (Test-Path "VERSION") { (Get-Content VERSION -Raw).Trim() } else { "unknown" }
Write-Host "[ok] Updated: $oldVersion -> $newVersion ($newRef)"

# ── post-update: rebuild LSP servers ────────────────────────────────────────

if (-not $SkipLsp) {
    Write-Host ""
    Write-Host "Rebuilding LSP servers..."

    foreach ($lsp in @("enma-lsp", "angel-lsp-pcx")) {
        $lspDir = Join-Path $ToolkitDir "lsp\$lsp"
        if (Test-Path $lspDir) {
            Write-Host "  $lsp..."
            Push-Location $lspDir
            try {
                npm install --silent 2>$null
                npm run compile 2>$null
                Write-Host "    [ok]"
            } catch {
                Write-Host "    [warn] build failed — run manually: cd $lspDir ; npm install ; npm run compile"
            }
            Pop-Location
        }
    }
}
# ── post-update: rebuild Rust core parser ───────────────────────────────────
$cargo = Get-Command cargo -ErrorAction SilentlyContinue
if (-not $SkipLsp -and $cargo) {
    Write-Host ""
    Write-Host "Rebuilding Rust core parser (pe-parser.exe)..."
    $parserDir = Join-Path $ToolkitDir "tools\pe-parser"
    $binDir = Join-Path $ToolkitDir "tools\bin"
    Push-Location $parserDir
    try {
        & cargo build --release 2>&1 | Out-Null
        New-Item -ItemType Directory -Force -Path $binDir | Out-Null
        Copy-Item (Join-Path $parserDir "target\release\pe-parser.exe") (Join-Path $binDir "pe-parser.exe") -Force -ErrorAction SilentlyContinue
        if (Test-Path (Join-Path $binDir "pe-parser.exe")) {
            Write-Host "  [ok] Rust core parser rebuilt: tools\bin\pe-parser.exe"
        } else {
            Write-Host "  [warn] Rust core build failed — falling back to Python" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "  [warn] Rust core build failed — falling back to Python" -ForegroundColor Yellow
    } finally {
        Pop-Location
    }
}

# ── post-update: refresh AI skills ───────────────────────────────────────────

if (-not $SkipSkills -and (Test-Path "$env:USERPROFILE\.claude")) {
    Write-Host ""
    Write-Host "Refreshing AI skills..."
    $skillsDir = Join-Path $ToolkitDir ".claude\skills"
    $destDir = Join-Path $env:USERPROFILE ".claude\skills"

    if (Test-Path $skillsDir) {
        $count = 0
        Get-ChildItem -Path $skillsDir -Directory | ForEach-Object {
            $skillName = $_.Name
            $dest = Join-Path $destDir $skillName
            New-Item -ItemType Directory -Path $dest -Force | Out-Null
            Copy-Item -Path "$($_.FullName)\*.md" -Destination $dest -Force -ErrorAction SilentlyContinue
            $count++
        }
        Write-Host "  [ok] $count skills refreshed"
    }
}

# ── post-update: regenerate knowledge bundles ───────────────────────────────

if (-not $SkipBundles) {
    Write-Host ""
    Write-Host "Checking knowledge bundles..."
    $builder = Join-Path $ToolkitDir "tools\build-llms-index.py"
    if (Test-Path $builder) {
        $checkResult = python3 $builder --check 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  [ok] Bundles in sync"
        } else {
            Write-Host "  Bundles out of sync — regenerating..."
            python3 $builder --quiet 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-Host "  [ok] Bundles regenerated"
            } else {
                Write-Host "  [warn] Bundle regeneration failed — run: python3 tools\build-llms-index.py"
            }
        }
    }
}

# ── done ─────────────────────────────────────────────────────────────────────

Write-Host ""
Write-Host "Update complete."
Write-Host "  Version:  $newVersion"
Write-Host "  Commit:   $newRef"
Write-Host "  Branch:   $currentBranch"
if (-not $SkipLsp)     { Write-Host "  LSP:      rebuilt" }
$binDir = Join-Path $ToolkitDir "tools\bin"
$cargo = Get-Command cargo -ErrorAction SilentlyContinue
if (-not $SkipLsp -and $cargo -and (Test-Path (Join-Path $binDir "pe-parser.exe"))) { Write-Host "  Rust:     rebuilt" }
if (-not $SkipSkills)   { Write-Host "  Skills:   refreshed" }
if (-not $SkipBundles)  { Write-Host "  Bundles:  checked" }
