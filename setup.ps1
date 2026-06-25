param(
    [string]$Project = ""
)

$ErrorActionPreference = "Stop"
$ToolkitDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "pcx-ai-toolkit setup"
Write-Host "Location: $ToolkitDir"

foreach ($cmd in @("git", "node", "npm", "cargo")) {
    if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) {
        Write-Error "ERROR: '$cmd' is required but not found on PATH."
        exit 1
    }
}

Write-Host "Building Rust tools..."
Push-Location (Join-Path $ToolkitDir "tools\pe-parser")
try {
    cargo build --release
} finally {
    Pop-Location
}

$bin = Join-Path $ToolkitDir "tools\bin"
New-Item -ItemType Directory -Force -Path $bin | Out-Null
$tools = @(
    "pe-parser", "pcx-rs", "api-lookup", "pattern-format-converter",
    "sig-uniqueness-checker", "binary-diff-summary", "offset-diff",
    "anti-debug-scanner", "identify-protector", "pe-section-analyzer",
    "analyze-vmprotect", "dump-strings-xor", "module-export-mapper"
)
foreach ($tool in $tools) {
    Copy-Item (Join-Path $ToolkitDir "tools\pe-parser\target\release\$tool.exe") (Join-Path $bin "$tool.exe") -Force
}

$version = if (Test-Path (Join-Path $ToolkitDir "VERSION")) { Get-Content (Join-Path $ToolkitDir "VERSION") -Raw } else { "unknown" }
Write-Host "Version: $($version.Trim())"
Write-Host "Setup complete. Add to PATH: $bin"
Write-Host "Quick start: pcx-rs doctor"
