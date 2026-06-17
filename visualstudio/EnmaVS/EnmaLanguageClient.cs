using Microsoft.VisualStudio.LanguageServer.Client;
using Microsoft.VisualStudio.Threading;
using Microsoft.VisualStudio.Utilities;
using System;
using System.Collections.Generic;
using System.ComponentModel.Composition;
using System.Diagnostics;
using System.IO;
using System.Reflection;
using System.Threading;
using System.Threading.Tasks;
using Task = System.Threading.Tasks.Task;

namespace PcxEnmaVS
{
    // LSP client for the Enma language server. Visual Studio activates this when
    // an .em file is opened (via the "enma" content type). It launches the bundled
    // Node.js server over stdio.
    //
    // Requires Node.js 18+ on PATH. The server payload ships in the VSIX under Server/.
    [ContentType("enma")]
    [Export(typeof(ILanguageClient))]
    [RunOnContext(RunningContext.RunOnHost)]
    public class EnmaLanguageClient : ILanguageClient
    {
        public string Name => "Enma Language Server (Perception.cx)";

        public IEnumerable<string> ConfigurationSections => null;

        public object InitializationOptions => null;

        public IEnumerable<string> FilesToWatch => null;

        public bool ShowNotificationOnInitializeFailed => true;

        public event AsyncEventHandler<EventArgs> StartAsync;
        public event AsyncEventHandler<EventArgs> StopAsync;

        public async Task<Connection> ActivateAsync(CancellationToken token)
        {
            await Task.Yield();

            string extensionDir = Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location);
            // The bin launcher auto-injects --stdio and resolves ../server/dist/server.js.
            string serverEntry = Path.Combine(extensionDir, "Server", "bin", "enma-language-server.js");

            if (!File.Exists(serverEntry))
            {
                // Surfaced to the user via the VS InfoBar.
                throw new FileNotFoundException(
                    "Enma language server not found in the extension. Expected: " + serverEntry);
            }

            var info = new ProcessStartInfo
            {
                FileName = "node",
                Arguments = "\"" + serverEntry + "\" --stdio",
                RedirectStandardInput = true,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                UseShellExecute = false,
                CreateNoWindow = true,
                WorkingDirectory = Path.Combine(extensionDir, "Server"),
            };

            var process = new Process { StartInfo = info };

            if (process.Start())
            {
                return new Connection(process.StandardOutput.BaseStream, process.StandardInput.BaseStream);
            }

            return null;
        }

        public async Task OnLoadedAsync()
        {
            var handler = StartAsync;
            if (handler != null)
            {
                await handler.InvokeAsync(this, EventArgs.Empty);
            }
        }

        public Task OnServerInitializedAsync() => Task.CompletedTask;

        public Task<InitializationFailureContext> OnServerInitializeFailedAsync(ILanguageClientInitializationInfo initializationState)
        {
            string message = "Enma language server failed to start. " +
                              "Ensure Node.js 18+ is installed and on your PATH (https://nodejs.org/). " +
                              initializationState?.StatusMessage;
            var failureContext = new InitializationFailureContext { FailureMessage = message };
            return Task.FromResult(failureContext);
        }
    }
}
