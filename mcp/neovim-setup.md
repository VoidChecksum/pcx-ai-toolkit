# Setting Up pcx-ai-toolkit with Neovim and Helix

This guide configures the Enma and AngelScript language servers for Neovim and Helix editors.

## Prerequisites

- Run `pcx setup` first to build the LSP servers
- Neovim 0.10+ **or** Helix 24.03+
- Node.js 18+ on PATH

Verify your LSP servers are built:
```bash
pcx doctor
# or manually:
ls lsp/enma-lsp/server/dist/server.js
ls lsp/angel-lsp-pcx/server/out/server.js
```

---

## Neovim Setup

### Using lazy.nvim

Add to your lazy.nvim plugin spec:

```lua
-- ~/.config/nvim/lua/plugins/pcx-lsp.lua
return {
  {
    "neovim/nvim-lspconfig",
    config = function()
      local lspconfig = require("lspconfig")
      local configs = require("lspconfig.configs")

      -- Adjust this path to where you cloned pcx-ai-toolkit
      local pcx_toolkit = vim.fn.expand("~/pcx-ai-toolkit")

      -- ── Register Enma LSP ─────────────────────────────────────────────
      if not configs.enma_lsp then
        configs.enma_lsp = {
          default_config = {
            cmd = {
              "node",
              pcx_toolkit .. "/lsp/enma-lsp/server/dist/server.js",
              "--stdio",
            },
            filetypes = { "enma" },
            root_dir = lspconfig.util.root_pattern(".git", "main.em", "*.em"),
            settings = {},
          },
        }
      end

      -- ── Register AngelScript LSP ──────────────────────────────────────
      if not configs.angelscript_lsp then
        configs.angelscript_lsp = {
          default_config = {
            cmd = {
              "node",
              pcx_toolkit .. "/lsp/angel-lsp-pcx/server/out/server.js",
              "--stdio",
            },
            filetypes = { "angelscript" },
            root_dir = lspconfig.util.root_pattern(".git", "main.as", "*.as"),
            settings = {},
          },
        }
      end

      lspconfig.enma_lsp.setup({
        on_attach = function(client, bufnr)
          -- Optional: bind LSP keymaps here
        end,
      })
      lspconfig.angelscript_lsp.setup({})
    end,
  },
}
```

### File Type Detection

Add to your Neovim config (`~/.config/nvim/init.lua` or a dedicated `ftdetect` file):

```lua
-- ~/.config/nvim/lua/ftdetect.lua  (require it from init.lua)
vim.filetype.add({
  extension = {
    em = "enma",
    as = "angelscript",
  },
})
```

Or as a Vimscript ftdetect file:

```vim
" ~/.config/nvim/ftdetect/enma.vim
autocmd BufRead,BufNewFile *.em set filetype=enma

" ~/.config/nvim/ftdetect/angelscript.vim
autocmd BufRead,BufNewFile *.as set filetype=angelscript
```

### Editor Settings for Enma Files

```vim
" ~/.config/nvim/ftplugin/enma.vim
setlocal commentstring=//\ %s
setlocal expandtab
setlocal shiftwidth=4
setlocal tabstop=4
setlocal colorcolumn=100
```

### Key LSP Bindings

Recommended keybindings to add in your `on_attach` callback:

```lua
local function on_attach(client, bufnr)
  local opts = { noremap = true, silent = true, buffer = bufnr }
  vim.keymap.set("n", "gd",  vim.lsp.buf.definition,     opts)
  vim.keymap.set("n", "K",   vim.lsp.buf.hover,           opts)
  vim.keymap.set("n", "grn", vim.lsp.buf.rename,          opts)
  vim.keymap.set("n", "gra", vim.lsp.buf.code_action,     opts)
  vim.keymap.set("n", "[d",  vim.diagnostic.goto_prev,    opts)
  vim.keymap.set("n", "]d",  vim.diagnostic.goto_next,    opts)
end
```

### MCP Integration (mcphub.nvim)

To use the `pcx-knowledge-mcp` server from within Neovim, install [mcphub.nvim](https://github.com/ravitemer/mcphub.nvim):

```lua
{
  "ravitemer/mcphub.nvim",
  config = function()
    require("mcphub").setup({
      servers = {
        ["pcx-knowledge"] = {
          command = "python3",
          args = { "-m", "server" },
          cwd = vim.fn.expand("~/pcx-ai-toolkit/mcp/pcx-knowledge-mcp"),
        },
      },
    })
  end,
}
```

---

## Helix Setup

Helix uses `~/.config/helix/languages.toml` for language server configuration.

### languages.toml

Add to `~/.config/helix/languages.toml`:

```toml
# ── Enma ──────────────────────────────────────────────────────────────────────
[[language]]
name = "enma"
scope = "source.enma"
file-types = ["em"]
roots = [".git", "main.em"]
comment-token = "//"
indent = { tab-width = 4, unit = "    " }
language-servers = ["enma-lsp"]

# ── AngelScript ───────────────────────────────────────────────────────────────
[[language]]
name = "angelscript"
scope = "source.angelscript"
file-types = ["as"]
roots = [".git", "main.as"]
comment-token = "//"
indent = { tab-width = 4, unit = "    " }
language-servers = ["angelscript-lsp"]

# ── Language Server Definitions ───────────────────────────────────────────────
[language-server.enma-lsp]
command = "node"
# Replace /path/to with your actual toolkit location
args = ["/path/to/pcx-ai-toolkit/lsp/enma-lsp/server/dist/server.js", "--stdio"]

[language-server.angelscript-lsp]
command = "node"
args = ["/path/to/pcx-ai-toolkit/lsp/angel-lsp-pcx/server/out/server.js", "--stdio"]
```

Replace `/path/to/pcx-ai-toolkit` with your actual path (e.g. `/home/user/pcx-ai-toolkit` or `C:/Users/user/pcx-ai-toolkit`).

### Helix Config Check

After editing `languages.toml`, verify with:
```bash
hx --health enma
hx --health angelscript
```

You should see the LSP listed as available. If not, check that `node` is on PATH and the server `.js` files exist.

### Helix Usage Tips

- **`gd`** — go to definition
- **`K`** — show hover documentation
- **`<space>a`** — code actions
- **`<space>d`** — show diagnostics

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| LSP not starting in Neovim | Run `:LspInfo` — check the `cmd` path resolves correctly |
| LSP not starting in Helix | Run `hx --health <lang>` to see LSP status |
| File type not detected (Neovim) | Check your `vim.filetype.add` or `ftdetect/enma.vim` file |
| File type not detected (Helix) | Verify `file-types = ["em"]` in `languages.toml` |
| `node: command not found` | Ensure Node.js 18+ is on PATH (`node --version`) |
| `server.js` not found | Run `pcx setup` or build manually: `cd lsp/enma-lsp && npm install && npm run compile` |

Run `pcx doctor` to diagnose all LSP-related issues automatically.
