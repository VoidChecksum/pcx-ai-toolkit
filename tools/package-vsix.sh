#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "==> Packaging Enma VS Code extension"
(
  cd "$ROOT/lsp/enma-lsp"
  npm install
  npm run compile
  npm run package
)


echo "==> VS Code packages"
ls -lh "$ROOT"/lsp/enma-lsp/*.vsix

if command -v msbuild >/dev/null 2>&1; then
  echo "==> Packaging Visual Studio extensions with msbuild"
  msbuild "$ROOT/visualstudio/EnmaVS/EnmaVS.csproj" /p:Configuration=Release /restore
else
  echo "==> Skipping Visual Studio .vsix packages: msbuild/VSSDK is not available on this host."
  echo "    Build them on Windows with the Visual Studio extension development workload."
fi
