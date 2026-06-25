# Visual Studio Extensions

Native **Visual Studio 2022** extension for Enma (`.em`) — completion, hover docs, and diagnostics via the same language servers used by the VS Code extensions.

> Visual Studio and VS Code use different extension models. A VS Code `.vsix` will **not** install in Visual Studio, and vice versa. These projects produce VS-compatible `.vsix` packages.

## Install (prebuilt)

Prebuilt VS `.vsix` files are attached to each [release](https://github.com/VoidChecksum/pcx-ai-toolkit/releases) (filename `PcxEnmaVS.vsix`).

1. Download the `.vsix`
2. Double-click it, or in Visual Studio: **Extensions → Manage Extensions → Install from VSIX**
3. Restart Visual Studio
4. Open a `.em` file — the language server starts automatically

**Requirement:** [Node.js 18+](https://nodejs.org/) on your `PATH`. The extension launches the bundled language server with `node`.

## How it works

The extension is a MEF `ILanguageClient` (the Microsoft-recommended way to add an LSP language to Visual Studio). When you open a matching file:

1. VS loads the client for the registered content type (`.em` → `enma`)
2. `ActivateAsync` launches `node Server/...server.js --stdio`
3. VS speaks LSP to the server over stdio

The Node.js language server payload is bundled inside the `.vsix` under `Server/`.

## Build from source

VS extensions require **Windows + MSBuild + the Visual Studio extension development workload** (VSSDK). They cannot be built on Linux/macOS.

```powershell
# 1. Build the language servers (from repo root)
cd lsp\enma-lsp; npm install; npm run compile; cd ..\..

# 2. Stage the server payloads
#    Enma: bin\ + server\dist\ -> visualstudio\EnmaVS\Server\

# 3. Build the VSIX
msbuild visualstudio\EnmaVS\EnmaVS.csproj /p:Configuration=Release /restore
```

The exact staging commands are in [`.github/workflows/release.yml`](../.github/workflows/release.yml), which builds the `.vsix` on every release tag.

## Project layout

```
visualstudio/
├── EnmaVS/
│   ├── EnmaVS.csproj                 VSIX project (net472, VSSDK BuildTools)
│   ├── source.extension.vsixmanifest VS 2022 manifest, MEF component asset
│   ├── EnmaLanguageClient.cs         ILanguageClient — launches node server
│   ├── EnmaContentDefinition.cs      .em -> "enma" content type
│   └── Server/                       node payload (populated at build time)
```

## License

The VS extension code in this directory is MIT (toolkit license). The bundled language server is an MIT build of [enma-lsp](https://github.com/sinnafuls/enma-lsp).
