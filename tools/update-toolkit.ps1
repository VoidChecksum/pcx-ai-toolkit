param(
    [switch]$Check,
    [switch]$Force
)

$ErrorActionPreference = "Stop"
$ToolkitDir = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $ToolkitDir

if ($Check) {
    git fetch --quiet
    $local = git rev-parse HEAD
    $remote = git rev-parse '@{u}'
    if ($local -eq $remote) {
        Write-Host "[ok] Toolkit is up to date"
        exit 0
    }
    Write-Host "[update] Local $local differs from upstream $remote"
    exit 1
}

git pull --ff-only

$pcx = Join-Path $ToolkitDir "tools\bin\pcx-rs.exe"
if ($Force -or -not (Test-Path $pcx)) {
    Write-Host "Building Rust tools..."
    Push-Location (Join-Path $ToolkitDir "tools\pe-parser")
    try { cargo build --release } finally { Pop-Location }
    $bin = Join-Path $ToolkitDir "tools\bin"
    New-Item -ItemType Directory -Force -Path $bin | Out-Null
    foreach ($tool in @("pe-parser", "pcx-rs", "api-lookup", "pattern-format-converter", "sig-uniqueness-checker", "binary-diff-summary", "offset-diff", "anti-debug-scanner", "identify-protector", "pe-section-analyzer", "analyze-vmprotect", "dump-strings-xor", "module-export-mapper")) {
        Copy-Item (Join-Path $ToolkitDir "tools\pe-parser\target\release\$tool.exe") (Join-Path $bin "$tool.exe") -Force
    }
}

Write-Host "[ok] pcx-ai-toolkit updated"
